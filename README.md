# Digital Store Bot

A modern, high-performance Telegram e-commerce bot built with **FastAPI + aiogram**. This bot provides a complete digital product sales platform with multi-gateway payments, automated delivery, and comprehensive admin management.

## 🌟 Features

### 🛍️ E-commerce Core
- **Digital Product Catalog** - Software, games, subscriptions, digital content
- **Multi-Payment Support** - Telegram Stars (built-in) + Cryptomus (crypto)
- **Automated Delivery** - Instant product delivery with customizable templates
- **Inventory Management** - Stock tracking with unlimited/limited quantities
- **Order Processing** - Complete order lifecycle with status tracking

### 👥 User Management
- **Trial System** - Free trial access for new users
- **Referral Program** - Multi-level referral rewards
- **User Profiles** - Activity tracking and purchase history
- **Admin Panel** - Comprehensive user and system management

### 🏗️ Modern Architecture
- **FastAPI Backend** - High-performance async API with automatic docs
- **aiogram 3.x** - Modern Telegram bot framework
- **SQLAlchemy 2.x** - Async ORM with type safety
- **Pydantic** - Data validation and serialization
- **Background Tasks** - Automated cleanup and maintenance
- **Docker Ready** - Production deployment with Docker Compose

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Docker & Docker Compose (recommended)
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Docker Installation (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <repository-url>
   cd digital-store
   cp .env.example .env
   ```

2. **Configure environment:**
   Edit `.env` file with your settings:
   ```bash
   BOT_TOKEN=your_bot_token_here
   BOT_DOMAIN=yourdomain.com  # For webhooks
   ADMIN_IDS=123456789
   DEVELOPER_ID=123456789
   ```

3. **Start services:**
   ```bash
   docker compose up -d
   ```

4. **Check status:**
   ```bash
   docker compose logs -f bot
   curl http://localhost:8000/api/webhooks/health
   ```

### Development Installation

1. **Setup Python environment:**
   ```bash
   pip install poetry
   poetry install
   ```

2. **Initialize database:**
   ```bash
   alembic upgrade head
   ```

3. **Run in development mode:**
   ```bash
   python -m app.main
   ```

## 📋 Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BOT_TOKEN` | ✅ | - | Telegram bot token |
| `BOT_DOMAIN` | ⚠️ | - | Domain for webhooks (production) |
| `ADMIN_IDS` | ✅ | - | Comma-separated admin IDs |
| `DEVELOPER_ID` | ✅ | - | Developer Telegram ID |
| `DATABASE_URL` | ⭕ | sqlite+aiosqlite:///./data/store.db | Database connection |
| `REDIS_URL` | ⭕ | redis://redis:6379/0 | Redis connection |
| `TELEGRAM_STARS_ENABLED` | ⭕ | true | Enable Telegram Stars |
| `CRYPTOMUS_ENABLED` | ⭕ | false | Enable Cryptomus payments |
| `TRIAL_ENABLED` | ⭕ | true | Enable trial system |
| `REFERRAL_ENABLED` | ⭕ | true | Enable referral program |

### Product Configuration

Products are defined in `data/products.json`:

```json
{
  "categories": ["software", "gaming", "subscription", "digital", "education"],
  "products": [
    {
      "name": "Premium Software License",
      "description": "Professional software with full features",
      "category": "software",
      "price": 999.99,
      "currency": "RUB",
      "delivery_type": "license_key",
      "duration_days": 365,
      "delivery_config": {
        "template": "🔑 Your license: {license_key}",
        "key_format": "XXXXX-XXXXX-XXXXX-XXXXX-XXXXX"
      },
      "is_active": true,
      "is_featured": true
    }
  ]
}
```

## 🏗️ Architecture Overview

### Core Components

```
digital-store/
├── app/
│   ├── main.py              # FastAPI application entry
│   ├── config.py            # Pydantic settings management
│   ├── database.py          # SQLAlchemy async setup
│   ├── models/              # Database models
│   ├── schemas/             # Pydantic request/response models
│   ├── services/            # Business logic layer
│   ├── bot/                 # Telegram bot handlers
│   │   ├── handlers/        # Message and callback handlers
│   │   ├── keyboards.py     # Inline keyboard layouts
│   │   └── middleware.py    # User management middleware
│   ├── api/                 # FastAPI routes
│   │   ├── webhooks.py      # Payment gateway webhooks
│   │   └── admin.py         # Admin API endpoints
│   ├── tasks/               # Background job scheduler
│   └── utils/               # Helper utilities
├── alembic/                 # Database migrations
├── data/                    # Runtime data (SQLite, JSON)
└── docker-compose.yml       # Production deployment
```

### Design Principles

- **Pragmatic over Perfect** - Simple, maintainable solutions
- **Service-Oriented** - Clear separation of business logic
- **Type-Safe** - Comprehensive type hints with Pydantic
- **Async-First** - Full async/await support throughout
- **Production-Ready** - Docker, health checks, graceful shutdown

## 💳 Payment Gateways

### Telegram Stars (Built-in)
```bash
TELEGRAM_STARS_ENABLED=true
# No additional configuration needed
```

### Cryptomus (Cryptocurrency)
```bash
CRYPTOMUS_ENABLED=true
CRYPTOMUS_API_KEY=your_api_key
CRYPTOMUS_MERCHANT_ID=your_merchant_id
```

Set webhook URL in Cryptomus dashboard:
`https://yourdomain.com/api/webhooks/cryptomus`

## 🔧 Development

### Commands

```bash
# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Code formatting
black app/
isort app/

# Type checking
mypy app/

# Testing
pytest
pytest --cov=app

# Run specific handler tests
pytest tests/test_bot_handlers.py -v
```

### Project Structure

- **Models** (`app/models/`) - SQLAlchemy database models
- **Schemas** (`app/schemas/`) - Pydantic validation models  
- **Services** (`app/services/`) - Business logic with dependency injection
- **Handlers** (`app/bot/handlers/`) - Telegram bot interaction logic
- **API** (`app/api/`) - FastAPI routes for webhooks and admin
- **Tasks** (`app/tasks/`) - Background job processing

### Adding New Features

1. **Database Model** - Create in `app/models/`
2. **Pydantic Schema** - Define in `app/schemas/`
3. **Service Logic** - Implement in `app/services/`
4. **Bot Handler** - Add to `app/bot/handlers/`
5. **Migration** - Generate with alembic
6. **Tests** - Add comprehensive test coverage

## 📊 Admin Features

### Bot Commands
- `/admin` - Access admin panel
- `/find_user [id]` - Find user by Telegram ID
- `/ban_user [id]` - Ban user
- `/unban_user [id]` - Unban user

### Admin Panel Features
- **📊 Statistics** - Users, products, orders, revenue
- **👥 User Management** - View, ban, manage users
- **📦 Product Management** - Import/export, stock management
- **🛒 Order Management** - View orders, process refunds
- **📢 Broadcasting** - Send messages to all users
- **⚙️ Settings** - System configuration

### API Endpoints
- `GET /api/admin/stats/users` - User statistics
- `GET /api/admin/stats/products` - Product statistics
- `GET /api/admin/stats/orders` - Order statistics
- `POST /api/admin/users/{id}/ban` - Ban user
- `POST /api/admin/orders/cleanup` - Cleanup expired orders

## 🔄 Background Tasks

Automated maintenance tasks:
- **Order Cleanup** - Expire pending orders (every 15 minutes)
- **System Stats** - Log daily statistics (daily at midnight)
- **Referral Processing** - Process pending rewards (hourly)
- **Database Backup** - Automatic backups (daily at 2 AM)

## 🚀 Production Deployment

### Docker Compose (Recommended)

```bash
# Production stack
docker compose up -d

# With nginx reverse proxy
docker compose --profile nginx up -d

# Database backup
docker compose --profile backup run backup
```

### Manual Deployment

```bash
# Install dependencies
poetry install --only=main

# Set environment
export ENVIRONMENT=production
export BOT_TOKEN=your_token

# Run migrations
alembic upgrade head

# Start application
python -m app.main
```

### Health Monitoring

- **Health Check**: `GET /api/webhooks/health`
- **Metrics**: Available via admin API
- **Logs**: Structured logging to files and stdout
- **Graceful Shutdown**: Proper cleanup of resources

## 🔒 Security Features

- **Input Validation** - Pydantic schema validation
- **SQL Injection Protection** - SQLAlchemy ORM
- **Rate Limiting** - Built-in middleware support
- **Webhook Verification** - Cryptographic signature validation
- **User Authentication** - Admin permission system
- **Data Sanitization** - HTML escaping and input cleaning

## 📈 Performance Optimizations

- **Async Operations** - Non-blocking I/O throughout
- **Connection Pooling** - SQLAlchemy and Redis pooling
- **Database Indexing** - Optimized queries with proper indexes
- **Caching** - Redis-based caching for frequently accessed data
- **Background Processing** - Non-blocking task execution

## 🐛 Troubleshooting

### Common Issues

**Bot not responding:**
```bash
# Check logs
docker compose logs bot --tail 50

# Verify webhook
curl -X GET "https://api.telegram.org/bot{BOT_TOKEN}/getWebhookInfo"

# Test health endpoint
curl http://localhost:8000/api/webhooks/health
```

**Database issues:**
```bash
# Check migration status
alembic current

# Apply migrations
alembic upgrade head

# Reset database (⚠️ DATA LOSS)
rm data/store.db && alembic upgrade head
```

**Payment webhook failures:**
- Verify webhook URLs in payment provider dashboard
- Check SSL certificate validity
- Review webhook signature verification logs

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📞 Support

- **Issues**: Create GitHub issue for bugs/features
- **Documentation**: Check inline code documentation
- **Community**: Join our discussion forums

---

Built with ❤️ using FastAPI + aiogram for modern, scalable Telegram bot development.