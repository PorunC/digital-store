"""Bot middleware."""
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser

from app.services.user_service import UserService
from app.schemas.user import UserCreate
from app.config import settings

logger = logging.getLogger(__name__)


class UserMiddleware(BaseMiddleware):
    """Middleware to handle user registration and activity tracking."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process the event."""
        user: TgUser = data.get("event_from_user")
        
        if user and not user.is_bot:
            # Get or create user
            db_user = await UserService.get_by_telegram_id(user.id)
            
            if not db_user:
                # Create new user
                user_data = UserCreate(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    language_code=user.language_code
                )
                
                # Check for referral code in start command
                referrer_code = None
                if hasattr(event, 'text') and event.text:
                    if event.text.startswith('/start '):
                        referrer_code = event.text.split(' ', 1)[1]
                
                db_user = await UserService.create_user(user_data, referrer_code)
                logger.info(f"New user registered: {user.id}")
            else:
                # Update user activity
                await UserService.update_activity(user.id)
            
            # Check if user is banned
            if db_user.is_banned:
                logger.warning(f"Banned user tried to use bot: {user.id}")
                return  # Don't process further
            
            # Add user to handler data
            data["db_user"] = db_user
        
        return await handler(event, data)


class AdminMiddleware(BaseMiddleware):
    """Middleware to check admin permissions."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process the event."""
        db_user = data.get("db_user")
        
        # Check if user is admin
        if db_user:
            is_admin = (
                db_user.is_admin or 
                db_user.telegram_id in settings.admin_ids or
                db_user.telegram_id == settings.developer_id
            )
            data["is_admin"] = is_admin
        else:
            data["is_admin"] = False
        
        return await handler(event, data)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging user interactions."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Process the event."""
        user: TgUser = data.get("event_from_user")
        
        if user and hasattr(event, 'text') and event.text:
            logger.info(f"User {user.id} ({user.username}): {event.text}")
        elif user and hasattr(event, 'data') and event.data:
            logger.info(f"User {user.id} ({user.username}) callback: {event.data}")
        
        return await handler(event, data)