#!/bin/bash
# ============================================================================
# FILE: scripts/prod.sh
# PURPOSE: Production environment management (All 4 Services)
# ============================================================================

set -e

COMPOSE_FILE="docker-compose.prod.yml"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_success() { echo -e "${GREEN}✓ $1${NC}"; }
print_error() { echo -e "${RED}✗ $1${NC}"; }
print_info() { echo -e "${YELLOW}ℹ $1${NC}"; }

# Create .env.production files if missing
check_env_files() {
    SERVICES=("image-service" "ghostscript-service" "pymupdf-service" "pypdf-service")
    
    for service in "${SERVICES[@]}"; do
        if [ ! -f "services/$service/.env.production" ]; then
            print_error ".env.production not found for $service"
            print_info "Please create services/$service/.env.production before deploying"
            exit 1
        fi
    done
}

# Start
prod_start() {
    print_info "Starting production environment..."
    
    # Check all .env.production files exist
    check_env_files
    
    docker-compose -f $COMPOSE_FILE up -d --build
    print_success "Production started!"
    print_info "Gateway: http://localhost"
    print_info "Redis: http://localhost:6379 (internal)"
    print_info "Health check: http://localhost/health"
    print_info ""
    print_info "Services:"
    print_info "  Image Service: http://localhost/api/image (via gateway)"
    print_info "  Ghostscript Service: http://localhost/api/ghostscript (via gateway)"
    print_info "  PyMuPDF Service: http://localhost/api/pymupdf (via gateway)"
    print_info "  PyPDF Service: http://localhost/api/pypdf (via gateway)"
}

# Stop
prod_stop() {
    print_info "Stopping..."
    docker-compose -f $COMPOSE_FILE down
    print_success "Stopped!"
}

# Restart
prod_restart() {
    print_info "Restarting..."
    docker-compose -f $COMPOSE_FILE restart
    print_success "Restarted!"
}

# Restart specific service
prod_restart_service() {
    SERVICE="${1:-}"
    if [ -z "$SERVICE" ]; then
        print_error "Service name required"
        echo "Usage: $0 restart-service SERVICE_NAME"
        echo "Example: $0 restart-service image-service"
        exit 1
    fi
    print_info "Restarting $SERVICE..."
    docker-compose -f $COMPOSE_FILE restart $SERVICE
    print_success "Restarted $SERVICE!"
}

# Logs
prod_logs() {
    SERVICE="${1:-}"
    if [ -z "$SERVICE" ]; then
        print_info "Showing all logs (Ctrl+C to exit)..."
        docker-compose -f $COMPOSE_FILE logs -f --tail=100
    else
        print_info "Showing logs for $SERVICE..."
        docker-compose -f $COMPOSE_FILE logs -f --tail=100 $SERVICE
    fi
}

# Rebuild
prod_rebuild() {
    print_info "Rebuilding all services..."
    docker-compose -f $COMPOSE_FILE down
    docker-compose -f $COMPOSE_FILE build --no-cache
    docker-compose -f $COMPOSE_FILE up -d
    print_success "Rebuilt!"
}

# Rebuild specific service
prod_rebuild_service() {
    SERVICE="${1:-}"
    if [ -z "$SERVICE" ]; then
        print_error "Service name required"
        echo "Usage: $0 rebuild-service SERVICE_NAME"
        echo "Example: $0 rebuild-service image-service"
        exit 1
    fi
    print_info "Rebuilding $SERVICE..."
    docker-compose -f $COMPOSE_FILE build --no-cache $SERVICE
    docker-compose -f $COMPOSE_FILE up -d $SERVICE
    print_success "Rebuilt $SERVICE!"
}

# Status
prod_status() {
    print_info "Container status:"
    docker-compose -f $COMPOSE_FILE ps
    echo ""
    print_info "Resource usage:"
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}" \
        zemrev_redis_prod zemrev_gateway_prod zemrev_image_prod zemrev_ghostscript_prod zemrev_pymupdf_prod zemrev_pypdf_prod 2>/dev/null || \
        docker stats --no-stream 2>/dev/null || \
        print_error "Could not get resource stats"
}

# Health check
prod_health() {
    print_info "Checking health..."
    echo ""
    
    # Gateway
    print_info "Gateway:"
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        print_success "Gateway: healthy"
    else
        print_error "Gateway: unhealthy"
    fi
    
    # Image Service
    print_info ""
    print_info "Image Service (Port 8000):"
    if docker-compose -f $COMPOSE_FILE exec -T image-service curl -sf http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Image Service: healthy"
    else
        print_error "Image Service: unhealthy"
    fi
    
    # PDF Service
    print_info ""
    print_info "PDF Service (Port 8001):"
    if docker-compose -f $COMPOSE_FILE exec -T ghostscript-service curl -sf http://localhost:8001/health > /dev/null 2>&1; then
        print_success "PDF Service: healthy"
    else
        print_error "PDF Service: unhealthy"
    fi
    
    # PyMuPDF Service
    print_info ""
    print_info "PyMuPDF Service (Port 8002):"
    if docker-compose -f $COMPOSE_FILE exec -T pymupdf-service curl -sf http://localhost:8002/health > /dev/null 2>&1; then
        print_success "PyMuPDF Service: healthy"
    else
        print_error "PyMuPDF Service: unhealthy"
    fi
    
    # PyPDF Service
    print_info ""
    print_info "PyPDF Service (Port 8003):"
    if docker-compose -f $COMPOSE_FILE exec -T pypdf-service curl -sf http://localhost:8003/health > /dev/null 2>&1; then
        print_success "PyPDF Service: healthy"
    else
        print_error "PyPDF Service: unhealthy"
    fi
    
    # Redis
    print_info ""
    print_info "Redis:"
    if docker exec zemrev_redis_prod redis-cli ping > /dev/null 2>&1; then
        print_success "Redis: healthy"
    else
        print_error "Redis: unhealthy"
    fi
}

# Queue status
prod_queue() {
    print_info "Queue status:"
    docker exec zemrev_redis_prod redis-cli INFO stats 2>/dev/null || \
        print_error "Could not get queue stats"
}

# Main
case "${1:-start}" in
    start) prod_start ;;
    stop) prod_stop ;;
    restart) prod_restart ;;
    restart-service) prod_restart_service "$2" ;;
    logs) prod_logs "$2" ;;
    rebuild) prod_rebuild ;;
    rebuild-service) prod_rebuild_service "$2" ;;
    status) prod_status ;;
    health) prod_health ;;
    queue) prod_queue ;;
    *)
        echo "Usage: $0 {start|stop|restart|restart-service|logs|rebuild|rebuild-service|status|health|queue}"
        echo ""
        echo "Examples:"
        echo "  $0 start                          # Start all services"
        echo "  $0 stop                           # Stop all services"
        echo "  $0 restart                        # Restart all services"
        echo "  $0 restart-service image-service  # Restart specific service"
        echo "  $0 logs                           # All logs"
        echo "  $0 logs image-service             # Specific service logs"
        echo "  $0 rebuild                        # Rebuild all services"
        echo "  $0 rebuild-service pdf-service    # Rebuild specific service"
        echo "  $0 status                         # Container status"
        echo "  $0 health                         # Health check all services"
        echo "  $0 queue                          # Queue statistics"
        exit 1
        ;;
esac