-- ============================================================================
-- FILE: services/api-gateway/lua/rate_limit.lua
-- PURPOSE: Redis-based rate limiting with auto-expiry (NO PERMANENT STORAGE)
-- ============================================================================

local redis = require "resty.redis"

local _M = {}

-- ⚠️ IMPORTANT: Keys auto-delete after 60 seconds (TTL)
-- No manual cleanup needed, no permanent storage

-- Service-specific rate limits (requests per minute)
local RATE_LIMITS = {
    ghostscript = { limit = 10, window = 60, message = "Ghostscript tool allows 10 requests per minute" },
    pymupdf = { limit = 14, window = 60, message = "PyMuPDF tool allows 14 requests per minute" },
    pypdf = { limit = 14, window = 60, message = "PyPDF tool allows 14 requests per minute" },
    image = { limit = 15, window = 60, message = "Image service allows 15 requests per minute" },
    ocr = { limit = 2, window = 60, message = "OCR service allows 2 requests per minute" }
}

-- Connect to Redis
local function connect_redis()
    local red = redis:new()
    red:set_timeouts(1000, 1000, 1000)  -- 1s timeouts
    
    local ok, err = red:connect("34.107.43.152", 6379)
    if not ok then
        ngx.log(ngx.ERR, "Failed to connect to Redis: ", err)
        return nil, err
    end
    
    return red
end

-- Check rate limit
function _M.check(service_name, identifier)
    -- Get service config
    local config = RATE_LIMITS[service_name]
    if not config then
        ngx.log(ngx.ERR, "Unknown service: ", service_name)
        return false, "Invalid service"
    end
    
    -- Connect to Redis
    local red, err = connect_redis()
    if not red then
        -- If Redis fails, allow request (fail open)
        ngx.log(ngx.WARN, "Redis unavailable, allowing request")
        return true
    end
    
    -- Rate limit key: ratelimit:<service>:<identifier>
    local key = "ratelimit:" .. service_name .. ":" .. identifier
    
    -- Get current count
    local count, err = red:get(key)
    if err then
        ngx.log(ngx.ERR, "Redis GET error: ", err)
        red:close()
        return true  -- Fail open
    end
    
    if count == ngx.null then
        count = 0
    else
        count = tonumber(count)
    end
    
    -- Check limit
    if count >= config.limit then
        -- Get TTL for retry info
        local ttl = red:ttl(key)
        
        -- Set custom error response
        ngx.status = 429
        ngx.header["Content-Type"] = "application/json"
        ngx.header["Retry-After"] = ttl
        ngx.header["X-RateLimit-Limit"] = config.limit
        ngx.header["X-RateLimit-Remaining"] = 0
        ngx.header["X-RateLimit-Reset"] = ngx.time() + ttl
        
        ngx.say('{"detail":"' .. config.message .. '","retry_after":' .. ttl .. '}')
        
        red:close()
        return ngx.exit(429)
    end
    
    -- Increment counter
    red:incr(key)
    
    -- Set expiry on first request
    if count == 0 then
        red:expire(key, config.window)
    end
    
    -- Get remaining requests
    local remaining = config.limit - count - 1
    
    -- Set rate limit headers
    ngx.header["X-RateLimit-Limit"] = config.limit
    ngx.header["X-RateLimit-Remaining"] = remaining
    
    -- Close connection
    local ok, err = red:set_keepalive(10000, 100)
    if not ok then
        ngx.log(ngx.WARN, "Failed to set keepalive: ", err)
    end
    
    return true
end

return _M