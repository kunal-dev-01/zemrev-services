# ============================================================================
# FILE: services/api-gateway/Dockerfile
# PURPOSE: OpenResty API Gateway with Redis Rate Limiting (Production)
# ============================================================================

FROM openresty/openresty:1.25.3.1-alpine

# Install wget for healthcheck
RUN apk add --no-cache wget

# Install lua-resty-redis (already included in OpenResty)
# Create lua directory
RUN mkdir -p /usr/local/openresty/nginx/lua

# Copy configs
COPY nginx.conf /usr/local/openresty/nginx/conf/nginx.conf
COPY lua/ /usr/local/openresty/nginx/lua/

# Non-root user (security)
RUN adduser -D -g 'nginx' nginxuser \
 && chown -R nginxuser:nginxuser /var/run/openresty /usr/local/openresty/nginx

USER nginxuser

# Health check
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost/health || exit 1

EXPOSE 80

STOPSIGNAL SIGTERM

CMD ["/usr/local/openresty/bin/openresty", "-g", "daemon off;"]