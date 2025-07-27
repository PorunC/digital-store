"""Main application entry point."""
import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from aiogram import Bot, Dispatcher
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

from app.config import settings
from app.database import init_database, close_database
from app.bot.handlers import start, catalog, order, admin
from app.bot.middleware import UserMiddleware, AdminMiddleware, LoggingMiddleware
from app.api.webhooks import router as webhooks_router
from app.api.admin import router as admin_api_router
from app.tasks.scheduler import start_scheduler, stop_scheduler

# Configure logging
handlers = [logging.StreamHandler(sys.stdout)]

# Only add file handler in production and if data directory is writable
if settings.is_production:
    try:
        # Create data directory if it doesn't exist
        settings.data_dir.mkdir(exist_ok=True)
        handlers.append(logging.FileHandler(settings.data_dir / "bot.log", encoding="utf-8"))
    except (PermissionError, OSError) as e:
        print(f"Warning: Could not create log file: {e}")

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format=settings.log_format,
    handlers=handlers
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Digital Store Bot...")
    
    # Initialize database
    await init_database()
    
    # Start background tasks
    await start_scheduler()
    
    # Load products from JSON if available
    from app.services.product_service import ProductService
    await ProductService.load_products_from_json()
    
    logger.info("Digital Store Bot started successfully!")
    
    yield
    
    logger.info("Shutting down Digital Store Bot...")
    
    # Stop background tasks
    await stop_scheduler()
    
    # Close database connections
    await close_database()
    
    logger.info("Digital Store Bot stopped.")


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Digital Store Bot",
        description="Telegram bot for selling digital products",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if not settings.is_production else None,
        redoc_url="/redoc" if not settings.is_production else None
    )
    
    # Add API routes
    app.include_router(webhooks_router, prefix="/api/webhooks")
    app.include_router(admin_api_router, prefix="/api/admin")
    
    return app


def setup_bot() -> tuple[Bot, Dispatcher]:
    """Setup bot and dispatcher."""
    # Create bot instance
    bot = Bot(token=settings.bot_token)
    
    # Create dispatcher
    dp = Dispatcher()
    
    # Add middlewares
    dp.message.middleware(LoggingMiddleware())
    dp.callback_query.middleware(LoggingMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    
    # Include routers
    dp.include_router(start.router)
    dp.include_router(catalog.router)
    dp.include_router(order.router)
    dp.include_router(admin.router)
    
    return bot, dp


async def setup_webhook(bot: Bot, dp: Dispatcher, app: FastAPI) -> None:
    """Setup webhook for bot."""
    if not settings.webhook_url:
        logger.error("Webhook URL not configured")
        return
    
    # Set webhook
    webhook_info = await bot.get_webhook_info()
    if webhook_info.url != settings.webhook_url:
        await bot.set_webhook(
            url=settings.webhook_url,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=True
        )
        logger.info(f"Webhook set to: {settings.webhook_url}")
    else:
        logger.info("Webhook already configured")
    
    # Create aiohttp app for webhook handling
    aiohttp_app = web.Application()
    
    # Setup webhook handler
    webhook_requests_handler = SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
    )
    webhook_requests_handler.register(aiohttp_app, path=settings.bot_webhook_path)
    
    # Mount aiohttp app to FastAPI
    setup_application(app, aiohttp_app, path="/")


async def start_polling(bot: Bot, dp: Dispatcher) -> None:
    """Start bot in polling mode."""
    logger.info("Starting bot in polling mode...")
    
    # Delete webhook
    await bot.delete_webhook(drop_pending_updates=True)
    
    # Start polling
    await dp.start_polling(bot, skip_updates=True)


async def main() -> None:
    """Main application function."""
    # Create FastAPI app
    app = create_app()
    
    # Setup bot
    bot, dp = setup_bot()
    
    if settings.webhook_url and not settings.debug:
        # Production mode with webhooks
        await setup_webhook(bot, dp, app)
        
        # Start FastAPI server
        import uvicorn
        config = uvicorn.Config(
            app,
            host=settings.host,
            port=settings.port,
            log_config=None  # Use our logging config
        )
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # Development mode with polling
        logger.info("Running in development mode with polling")
        
        async with app.router.lifespan_context(app):
            await start_polling(bot, dp)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)