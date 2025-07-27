#!/bin/bash

# Digital Store Bot Deployment Script
# Automated deployment script for production environments

set -e

# Configuration
PROJECT_NAME="digital-store-bot"
BACKUP_DIR="/var/backups/${PROJECT_NAME}"
LOG_FILE="/var/log/${PROJECT_NAME}/deploy.log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
    echo "[SUCCESS] $1" >> "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
    echo "[WARNING] $1" >> "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    echo "[ERROR] $1" >> "$LOG_FILE"
}

# Function to check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if running as root or with sudo
    if [[ $EUID -eq 0 ]]; then
        log_warning "Running as root"
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker not found"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose not found"
        exit 1
    fi
    
    # Check if .env exists
    if [ ! -f ".env" ]; then
        log_error ".env file not found"
        exit 1
    fi
    
    # Create log directory
    mkdir -p "$(dirname "$LOG_FILE")"
    
    log_success "Prerequisites check passed"
}

# Function to create backup
create_backup() {
    log "Creating backup..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup timestamp
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_NAME="${PROJECT_NAME}_backup_${TIMESTAMP}"
    
    # Backup database
    if [ -f "data/store.db" ]; then
        cp "data/store.db" "${BACKUP_DIR}/${BACKUP_NAME}.db"
        log_success "Database backup created: ${BACKUP_NAME}.db"
    fi
    
    # Backup configuration
    if [ -f ".env" ]; then
        cp ".env" "${BACKUP_DIR}/${BACKUP_NAME}.env"
    fi
    
    # Backup products
    if [ -f "data/products.json" ]; then
        cp "data/products.json" "${BACKUP_DIR}/${BACKUP_NAME}_products.json"
    fi
    
    # Clean old backups (keep last 10)
    cd "$BACKUP_DIR"
    ls -t ${PROJECT_NAME}_backup_*.db 2>/dev/null | tail -n +11 | xargs -r rm
    ls -t ${PROJECT_NAME}_backup_*.env 2>/dev/null | tail -n +11 | xargs -r rm
    ls -t ${PROJECT_NAME}_backup_*_products.json 2>/dev/null | tail -n +11 | xargs -r rm
    cd - > /dev/null
    
    log_success "Backup completed"
}

# Function to pull latest changes
pull_changes() {
    log "Pulling latest changes..."
    
    if [ -d ".git" ]; then
        git pull origin main
        log_success "Git pull completed"
    else
        log_warning "Not a git repository, skipping pull"
    fi
}

# Function to build new images
build_images() {
    log "Building Docker images..."
    
    # Pull base images first
    docker-compose pull --ignore-pull-failures
    
    # Build application image
    docker-compose build --no-cache bot
    
    log_success "Docker images built"
}

# Function to run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Check if bot service is running
    if docker-compose ps bot | grep -q "Up"; then
        docker-compose exec bot alembic upgrade head
    else
        # Start bot temporarily for migrations
        docker-compose up -d bot
        sleep 10
        docker-compose exec bot alembic upgrade head
        docker-compose stop bot
    fi
    
    log_success "Database migrations completed"
}

# Function to deploy services
deploy_services() {
    log "Deploying services..."
    
    # Stop services gracefully
    docker-compose stop
    
    # Start services
    docker-compose up -d
    
    # Wait for services to be healthy
    log "Waiting for services to be healthy..."
    for i in {1..30}; do
        if curl -f http://localhost:8000/api/webhooks/health >/dev/null 2>&1; then
            log_success "Services are healthy"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "Services failed to become healthy"
            exit 1
        fi
        
        sleep 2
    done
    
    log_success "Deployment completed"
}

# Function to verify deployment
verify_deployment() {
    log "Verifying deployment..."
    
    # Check service status
    docker-compose ps
    
    # Check health endpoint
    if curl -f http://localhost:8000/api/webhooks/health >/dev/null 2>&1; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        return 1
    fi
    
    # Check logs for errors
    if docker-compose logs --tail=50 bot | grep -i error; then
        log_warning "Errors found in logs"
    fi
    
    log_success "Deployment verification completed"
}

# Function to rollback deployment
rollback() {
    log_error "Rolling back deployment..."
    
    # Find latest backup
    LATEST_BACKUP=$(ls -t ${BACKUP_DIR}/${PROJECT_NAME}_backup_*.db 2>/dev/null | head -n1)
    
    if [ -n "$LATEST_BACKUP" ]; then
        # Stop services
        docker-compose stop
        
        # Restore database
        cp "$LATEST_BACKUP" "data/store.db"
        
        # Restore environment if available
        BACKUP_ENV="${LATEST_BACKUP%.db}.env"
        if [ -f "$BACKUP_ENV" ]; then
            cp "$BACKUP_ENV" ".env"
        fi
        
        # Restart services
        docker-compose up -d
        
        log_success "Rollback completed"
    else
        log_error "No backup found for rollback"
        exit 1
    fi
}

# Function to show status
show_status() {
    echo ""
    echo "==================== SERVICE STATUS ===================="
    docker-compose ps
    
    echo ""
    echo "==================== DISK USAGE ===================="
    df -h | grep -E "(Filesystem|/dev/)"
    
    echo ""
    echo "==================== DOCKER IMAGES ===================="
    docker images | grep digital-store
    
    echo ""
    echo "==================== RECENT LOGS ===================="
    docker-compose logs --tail=10 bot
}

# Function to cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove unused volumes (be careful!)
    # docker volume prune -f
    
    # Clean up old logs
    find logs/ -name "*.log" -mtime +7 -delete 2>/dev/null || true
    
    log_success "Cleanup completed"
}

# Main menu
show_help() {
    echo "Digital Store Bot Deployment Script"
    echo ""
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Options:"
    echo "  deploy      Full deployment (backup, build, deploy)"
    echo "  quick       Quick deployment (no backup, no build)"
    echo "  rollback    Rollback to previous version"
    echo "  status      Show service status"
    echo "  logs        Show recent logs"
    echo "  backup      Create backup only"
    echo "  migrate     Run database migrations only"
    echo "  cleanup     Clean up old resources"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy           # Full production deployment"
    echo "  $0 quick            # Quick restart without rebuild"
    echo "  $0 rollback         # Emergency rollback"
}

# Main function
main() {
    case "${1:-deploy}" in
        deploy)
            log "Starting full deployment..."
            check_prerequisites
            create_backup
            pull_changes
            build_images
            run_migrations
            deploy_services
            verify_deployment
            cleanup
            show_status
            log_success "Full deployment completed successfully!"
            ;;
        quick)
            log "Starting quick deployment..."
            check_prerequisites
            deploy_services
            verify_deployment
            log_success "Quick deployment completed!"
            ;;
        rollback)
            log "Starting rollback..."
            check_prerequisites
            rollback
            log_success "Rollback completed!"
            ;;
        status)
            show_status
            ;;
        logs)
            docker-compose logs -f bot
            ;;
        backup)
            check_prerequisites
            create_backup
            ;;
        migrate)
            check_prerequisites
            run_migrations
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
}

# Error handling
trap 'log_error "Deployment failed at line $LINENO. Exit code: $?"; exit 1' ERR

# Run main function
main "$@"