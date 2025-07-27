# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a modern Telegram e-commerce bot built with **FastAPI + aiogram** for selling digital products. The bot features multi-gateway payments, automated delivery, referral system, and comprehensive admin management.

## Development Commands

### Docker-based Development (Primary Method)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f bot
docker compose logs -f redis

# Restart specific service
docker compose restart bot

# Stop all services
docker compose down

# Rebuild and restart
docker compose build && docker compose up -d
```

### Local Development

```bash
# Install dependencies
poetry install

# Run database migrations
alembic upgrade head

# Start in development mode (polling)
python -m app.main

# Alternative entry point
python run.py
```

### Database Management

```bash
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Downgrade migration
alembic downgrade -1

# Check current revision
alembic current

# View migration history
alembic history
```

### Code Quality

```bash
# Format code
black app/
isort app/

# Type checking
mypy app/

# Run tests (if tests exist)
pytest
pytest --cov=app
pytest --cov=app --cov-report=html
```

### Production Deployment

```bash
# Deploy with script
./scripts/deploy.sh

# Manual deployment
docker compose --profile nginx up -d

# Database backup
docker compose --profile backup run backup
```

## Architecture Overview

### Core Structure

```
app/
├── main.py              # FastAPI + aiogram application entry
├── config.py            # Pydantic settings with environment management
├── database.py          # SQLAlchemy async session management
├── models/              # Database models (User, Product, Order, Referral)
├── schemas/             # Pydantic request/response models
├── services/            # Business logic layer
│   ├── user_service.py      # User management and authentication
│   ├── product_service.py   # Product catalog and JSON loading
│   ├── order_service.py     # Order processing and fulfillment
│   ├── payment_service.py   # Multi-gateway payment handling
│   └── notification_service.py # Admin and user notifications
├── bot/                 # Telegram bot implementation
│   ├── handlers/        # Message and callback handlers by feature
│   ├── keyboards.py     # Inline keyboard layouts
│   └── middleware.py    # User management and admin middleware
├── api/                 # FastAPI routes
│   ├── webhooks.py      # Payment gateway webhooks
│   └── admin.py         # Admin API endpoints
├── tasks/               # Background job scheduler
└── utils/               # Helper utilities
```

### Design Patterns

- **Service-Oriented Architecture**: Business logic separated into services with dependency injection
- **FastAPI + aiogram Integration**: FastAPI handles webhooks and admin API, aiogram handles bot interactions
- **Async-First**: Full async/await support with SQLAlchemy 2.x async sessions
- **Type-Safe**: Comprehensive type hints with Pydantic models for validation
- **Configuration Management**: Environment-based settings with Pydantic Settings

### Key Architectural Components

- **ServicesContainer Pattern**: Services are stateless classes with static methods
- **Database Session Management**: Async context managers for automatic cleanup
- **Middleware Chain**: User registration, admin checks, and logging middleware
- **Router-based Handlers**: Feature-specific handlers (start, catalog, order, admin)
- **Multi-Gateway Payments**: Pluggable payment system (Telegram Stars, Cryptomus)

## Configuration

### Required Environment Variables

```bash
# Core Bot Settings
BOT_TOKEN=your_bot_token_here
BOT_DOMAIN=yourdomain.com  # For production webhooks
ADMIN_IDS=123456789,987654321  # Comma-separated admin IDs
DEVELOPER_ID=123456789

# Database & Redis
DATABASE_URL=sqlite+aiosqlite:///./data/store.db  # Default SQLite
REDIS_URL=redis://redis:6379/0

# Payment Gateways
TELEGRAM_STARS_ENABLED=true
CRYPTOMUS_ENABLED=false
CRYPTOMUS_API_KEY=your_api_key
CRYPTOMUS_MERCHANT_ID=your_merchant_id

# Business Logic
TRIAL_ENABLED=true
REFERRAL_ENABLED=true
DEFAULT_CURRENCY=RUB
```

### Product Configuration

Products are defined in `data/products.json` with the following structure:
- **Categories**: software, gaming, subscription, digital, education
- **Delivery Types**: license_key, account_info, download_link, api_access
- **Stock Management**: Unlimited (null) or limited quantities
- **Delivery Templates**: Customizable message templates with variable substitution

## Development Workflow

### Adding New Features

1. **Database Model**: Create in `app/models/` following SQLAlchemy 2.x async patterns
2. **Pydantic Schema**: Define validation models in `app/schemas/`
3. **Service Logic**: Implement business logic in `app/services/` using static methods
4. **Database Migration**: Generate with `alembic revision --autogenerate`
5. **Bot Handler**: Add to appropriate handler in `app/bot/handlers/`
6. **API Endpoint**: Add to `app/api/` if external access needed
7. **Apply Migration**: Run `alembic upgrade head`

### Service Development Guidelines

- **Static Methods**: Services use static methods for stateless operations
- **Session Management**: Always use `async with get_session()` for database operations
- **Error Handling**: Log errors and return appropriate responses
- **Type Hints**: Use comprehensive type annotations for better IDE support

### Handler Development

- **Router Pattern**: Each feature has its own router (start, catalog, order, admin)
- **Middleware Chain**: User middleware automatically creates/fetches users from database
- **State Management**: Use aiogram FSM for multi-step interactions
- **Keyboard Layouts**: Centralized keyboard definitions in `app/bot/keyboards.py`

## Database Schema

### Core Models

- **User** (`app/models/user.py`): Telegram users with trial/referral state
- **Product** (`app/models/product.py`): Digital products with delivery configuration
- **Order** (`app/models/order.py`): Purchase orders with status tracking
- **Referral** (`app/models/referral.py`): Multi-level referral relationships

### Migration Workflow

1. Modify models in `app/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review generated migration in `alembic/versions/`
4. Apply migration: `alembic upgrade head`
5. Verify schema changes in database

## Payment Integration

### Telegram Stars (Built-in)
- No additional configuration required beyond `TELEGRAM_STARS_ENABLED=true`
- Automatically handles invoice creation and payment verification

### Cryptomus (Cryptocurrency)
- Requires API credentials and webhook configuration
- Webhook endpoint: `/api/webhooks/cryptomus`
- Handles multiple cryptocurrency payments

### Adding New Payment Gateways
1. Implement payment logic in `app/services/payment_service.py`
2. Add webhook handler in `app/api/webhooks.py`
3. Update configuration in `app/config.py`
4. Add environment variables for credentials

## Production Considerations

### Docker Deployment
- **Primary Stack**: bot + redis services
- **With Nginx**: Use `--profile nginx` for reverse proxy
- **Database Backup**: Use `--profile backup` for automated backups

### Health Monitoring
- **Health Check**: `GET /api/webhooks/health`
- **Container Health**: Built-in Docker healthchecks
- **Logging**: Structured logging to files and stdout

### Background Tasks
- **Order Cleanup**: Expires pending orders (15 minutes)
- **Referral Processing**: Processes pending rewards (hourly)
- **System Stats**: Daily statistics logging (midnight)

## Testing Strategy

Currently no test suite exists. When adding tests:
- Use `pytest` with `pytest-asyncio` for async test support
- Test database operations with async sessions
- Mock external services (Telegram API, payment gateways)
- Test handlers with aiogram test utilities

## Common Debugging

### Bot Not Responding
1. Check webhook configuration: `curl -X GET "https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"`
2. Verify domain resolution and SSL certificate
3. Check logs: `docker compose logs bot --tail 50`
4. Test health endpoint: `curl http://localhost:8000/api/webhooks/health`

### Database Issues
1. Check migration status: `alembic current`
2. Apply pending migrations: `alembic upgrade head`
3. Verify database file exists: `ls -la data/store.db`

### Payment Gateway Issues
- **Telegram Stars**: Verify bot token and BotFather payment settings
- **Cryptomus**: Check webhook URL accessibility and API credentials
- **General**: Review webhook signature verification in logs