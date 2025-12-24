# ============================================================================
# FILE: services/api-gateway/Dockerfile
# PURPOSE: OpenResty API Gateway (Cloudflare SSL + Redis Rate Limit)
# ============================================================================

FROM openresty/openresty:1.25.3.1-alpine

# Install wget for healthcheck
RUN apk add --no-cache wget

# Create required dirs
RUN mkdir -p \
    /usr/local/openresty/nginx/lua \
    /etc/nginx/ssl

# Copy nginx config & lua scripts
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY lua/ /usr/local/openresty/nginx/lua/

# Copy Cloudflare Origin SSL certs INTO IMAGE
COPY cf-origin.pem /etc/nginx/ssl/cf-origin.pem
COPY cf-origin.key /etc/nginx/ssl/cf-origin.key

# Secure permissions
RUN chmod 600 /etc/nginx/ssl/cf-origin.key \
 && chmod 644 /etc/nginx/ssl/cf-origin.pem

# Expose HTTP + HTTPS
EXPOSE 80 443

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

STOPSIGNAL SIGTERM

# IMPORTANT: Run as root (OpenResty will drop privileges internally)
CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]
