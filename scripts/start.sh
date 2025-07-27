#!/bin/bash

# Digital Store Bot - Start Script
# Usage: ./scripts/start.sh [development|production]

set -e

MODE=${1:-development}
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "🚀 Starting Digital Store Bot in $MODE mode..."

cd "$PROJECT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env with your configuration before continuing."
    exit 1
fi

# Check if data directory exists
if [ ! -d data ]; then
    echo "📁 Creating data directory..."
    mkdir -p data logs backups
fi

# Check if products.json exists
if [ ! -f data/products.json ]; then
    echo "📦 Products file not found. Using example products..."
    # products.json is already created by the script
fi

case $MODE in
    development)
        echo "🔧 Starting in development mode..."
        
        # Install dependencies if needed
        if [ ! -d .venv ] && command -v poetry &> /dev/null; then
            echo "📦 Installing dependencies with Poetry..."
            poetry install
        fi
        
        # Run database migrations
        echo "🗄️  Running database migrations..."
        if command -v poetry &> /dev/null; then
            poetry run alembic upgrade head
        else
            alembic upgrade head
        fi
        
        # Start the bot
        echo "🤖 Starting bot..."
        if command -v poetry &> /dev/null; then
            poetry run python -m app.main
        else
            python -m app.main
        fi
        ;;
        
    production)
        echo "🏭 Starting in production mode..."
        
        # Check required environment variables
        source .env
        if [ -z "$BOT_TOKEN" ]; then
            echo "❌ BOT_TOKEN is required"
            exit 1
        fi
        
        if [ -z "$BOT_DOMAIN" ]; then
            echo "❌ BOT_DOMAIN is required for production"
            exit 1
        fi
        
        # Use Docker Compose
        echo "🐳 Starting with Docker Compose..."
        docker compose up -d
        
        echo "✅ Bot started successfully!"
        echo "📊 View logs: docker compose logs bot -f"
        echo "🔍 Health check: curl http://localhost:8000/api/webhooks/health"
        ;;
        
    *)
        echo "❌ Invalid mode: $MODE"
        echo "Usage: $0 [development|production]"
        exit 1
        ;;
esac

echo "✅ Digital Store Bot started successfully in $MODE mode!"