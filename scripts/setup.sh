#!/bin/bash

# Digital Store Bot Setup Script
# This script helps set up the bot for development or production

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to check Docker installation
check_docker() {
    if command_exists docker && command_exists docker-compose; then
        print_success "Docker and Docker Compose are installed"
        return 0
    else
        print_error "Docker or Docker Compose not found"
        print_status "Please install Docker and Docker Compose first"
        print_status "Visit: https://docs.docker.com/get-docker/"
        return 1
    fi
}

# Function to setup environment file
setup_env() {
    print_status "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            print_success "Created .env file from .env.example"
        else
            print_error ".env.example not found"
            return 1
        fi
    else
        print_warning ".env file already exists, skipping..."
    fi
    
    print_warning "Please edit .env file with your configuration:"
    print_status "- BOT_TOKEN: Get from @BotFather"
    print_status "- BOT_DOMAIN: Your domain for webhooks"
    print_status "- ADMIN_IDS: Your Telegram user ID"
    print_status "- DEVELOPER_ID: Your Telegram user ID"
}

# Function to setup data directories
setup_directories() {
    print_status "Creating data directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p backups
    mkdir -p config
    
    # Create empty database file if it doesn't exist
    if [ ! -f "data/store.db" ]; then
        touch data/store.db
    fi
    
    print_success "Data directories created"
}

# Function to setup products
setup_products() {
    print_status "Setting up product catalog..."
    
    if [ ! -f "data/products.json" ]; then
        if [ -f "data/products.example.json" ]; then
            cp data/products.example.json data/products.json
            print_success "Created products.json from example"
        else
            print_warning "No products.example.json found, using default"
        fi
    else
        print_warning "products.json already exists, skipping..."
    fi
}

# Function to build Docker images
build_docker() {
    print_status "Building Docker images..."
    
    if ! docker compose build; then
        print_error "Failed to build Docker images"
        return 1
    fi
    
    print_success "Docker images built successfully"
}

# Function to start services
start_services() {
    print_status "Starting services..."
    
    if ! docker compose up -d; then
        print_error "Failed to start services"
        return 1
    fi
    
    print_success "Services started successfully"
    
    # Wait a moment for services to start
    sleep 5
    
    # Check service health
    print_status "Checking service health..."
    if curl -f http://localhost:8000/api/webhooks/health >/dev/null 2>&1; then
        print_success "Bot is running and healthy"
    else
        print_warning "Bot may still be starting up"
        print_status "Check logs with: docker compose logs -f bot"
    fi
}

# Function to run database migrations
run_migrations() {
    print_status "Running database migrations..."
    
    if ! docker compose exec bot alembic upgrade head; then
        print_error "Failed to run migrations"
        return 1
    fi
    
    print_success "Database migrations completed"
}

# Function to show status
show_status() {
    print_status "Service Status:"
    docker compose ps
    
    echo ""
    print_status "Useful commands:"
    echo "  docker compose logs -f bot     # View bot logs"
    echo "  docker compose restart bot     # Restart bot"
    echo "  docker compose down            # Stop all services"
    echo "  docker compose pull            # Update images"
    
    echo ""
    print_status "URLs:"
    echo "  Health Check: http://localhost:8000/api/webhooks/health"
    echo "  API Docs: http://localhost:8000/docs (development only)"
}

# Function for development setup
setup_development() {
    print_status "Setting up development environment..."
    
    # Check Python
    if ! command_exists python3; then
        print_error "Python 3 not found"
        return 1
    fi
    
    # Check Poetry
    if ! command_exists poetry; then
        print_error "Poetry not found"
        print_status "Install Poetry: curl -sSL https://install.python-poetry.org | python3 -"
        return 1
    fi
    
    # Install dependencies
    print_status "Installing Python dependencies..."
    poetry install
    
    # Setup pre-commit hooks
    if command_exists pre-commit; then
        print_status "Installing pre-commit hooks..."
        poetry run pre-commit install
    fi
    
    print_success "Development environment setup complete"
    print_status "Run with: poetry run python -m app.main"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    
    docker compose down
    docker system prune -f
    
    print_success "Cleanup complete"
}

# Main menu
show_menu() {
    echo ""
    echo "=========================================="
    echo "  Digital Store Bot Setup Script"
    echo "=========================================="
    echo ""
    echo "Choose an option:"
    echo "  1) Full Docker setup (production)"
    echo "  2) Development setup"
    echo "  3) Start services"
    echo "  4) Stop services"
    echo "  5) Show status"
    echo "  6) Run migrations"
    echo "  7) View logs"
    echo "  8) Cleanup"
    echo "  9) Exit"
    echo ""
}

# Main script logic
main() {
    if [ $# -eq 0 ]; then
        while true; do
            show_menu
            read -p "Enter your choice [1-9]: " choice
            
            case $choice in
                1)
                    print_status "Starting full Docker setup..."
                    check_docker || exit 1
                    setup_env
                    setup_directories
                    setup_products
                    build_docker
                    start_services
                    run_migrations
                    show_status
                    ;;
                2)
                    setup_development
                    ;;
                3)
                    start_services
                    ;;
                4)
                    docker compose down
                    print_success "Services stopped"
                    ;;
                5)
                    show_status
                    ;;
                6)
                    run_migrations
                    ;;
                7)
                    docker compose logs -f bot
                    ;;
                8)
                    cleanup
                    ;;
                9)
                    print_status "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option"
                    ;;
            esac
            
            echo ""
            read -p "Press Enter to continue..."
        done
    else
        # Handle command line arguments
        case $1 in
            --docker)
                check_docker || exit 1
                setup_env
                setup_directories
                setup_products
                build_docker
                start_services
                run_migrations
                show_status
                ;;
            --dev)
                setup_development
                ;;
            --start)
                start_services
                ;;
            --stop)
                docker compose down
                ;;
            --status)
                show_status
                ;;
            --migrate)
                run_migrations
                ;;
            --cleanup)
                cleanup
                ;;
            --help)
                echo "Usage: $0 [option]"
                echo ""
                echo "Options:"
                echo "  --docker    Full Docker setup"
                echo "  --dev       Development setup"
                echo "  --start     Start services"
                echo "  --stop      Stop services"
                echo "  --status    Show status"
                echo "  --migrate   Run migrations"
                echo "  --cleanup   Cleanup"
                echo "  --help      Show this help"
                ;;
            *)
                print_error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    fi
}

# Run main function
main "$@"