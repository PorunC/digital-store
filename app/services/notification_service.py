"""Notification service for sending messages to users and admins."""
import logging
from typing import List, Optional

from aiogram import Bot
from aiogram.enums import ParseMode

from app.config import settings

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for sending notifications."""
    
    def __init__(self, bot: Bot):
        self.bot = bot
    
    async def send_user_message(
        self,
        user_id: int,
        message: str,
        parse_mode: Optional[str] = ParseMode.HTML,
        disable_web_page_preview: bool = True
    ) -> bool:
        """Send message to a specific user."""
        try:
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode=parse_mode,
                disable_web_page_preview=disable_web_page_preview
            )
            logger.debug(f"Sent message to user {user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send message to user {user_id}: {e}")
            return False
    
    async def send_admin_message(
        self,
        message: str,
        parse_mode: Optional[str] = ParseMode.HTML
    ) -> int:
        """Send message to all admin users."""
        if not settings.admin_ids:
            logger.warning("No admin IDs configured")
            return 0
        
        sent_count = 0
        for admin_id in settings.admin_ids:
            success = await self.send_user_message(admin_id, message, parse_mode)
            if success:
                sent_count += 1
        
        logger.info(f"Sent admin message to {sent_count}/{len(settings.admin_ids)} admins")
        return sent_count
    
    async def send_developer_message(
        self,
        message: str,
        parse_mode: Optional[str] = ParseMode.HTML
    ) -> bool:
        """Send message to the developer."""
        if not settings.developer_id:
            logger.warning("No developer ID configured")
            return False
        
        return await self.send_user_message(settings.developer_id, message, parse_mode)
    
    async def broadcast_message(
        self,
        user_ids: List[int],
        message: str,
        parse_mode: Optional[str] = ParseMode.HTML
    ) -> dict:
        """Broadcast message to multiple users."""
        results = {
            "sent": 0,
            "failed": 0,
            "blocked": 0
        }
        
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=parse_mode,
                    disable_web_page_preview=True
                )
                results["sent"] += 1
                
            except Exception as e:
                error_str = str(e).lower()
                if "blocked" in error_str or "forbidden" in error_str:
                    results["blocked"] += 1
                else:
                    results["failed"] += 1
                    
                logger.debug(f"Failed to send broadcast to user {user_id}: {e}")
        
        logger.info(f"Broadcast results: {results}")
        return results
    
    async def notify_new_order(self, order_number: str, user_id: int, product_name: str, amount: str) -> None:
        """Notify admins about new order."""
        message = (
            f"🛒 <b>New Order</b>\n\n"
            f"Order: <code>{order_number}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Product: {product_name}\n"
            f"Amount: {amount}"
        )
        await self.send_admin_message(message)
    
    async def notify_order_completed(self, order_number: str, user_id: int, product_name: str) -> None:
        """Notify admins about completed order."""
        message = (
            f"✅ <b>Order Completed</b>\n\n"
            f"Order: <code>{order_number}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Product: {product_name}"
        )
        await self.send_admin_message(message)
    
    async def notify_payment_failed(self, order_number: str, user_id: int, reason: str) -> None:
        """Notify admins about failed payment."""
        message = (
            f"❌ <b>Payment Failed</b>\n\n"
            f"Order: <code>{order_number}</code>\n"
            f"User: <code>{user_id}</code>\n"
            f"Reason: {reason}"
        )
        await self.send_admin_message(message)
    
    async def notify_error(self, error_message: str, context: Optional[str] = None) -> None:
        """Notify developer about system errors."""
        message = f"🚨 <b>System Error</b>\n\n{error_message}"
        if context:
            message += f"\n\nContext: {context}"
        
        await self.send_developer_message(message)
    
    async def send_order_confirmation(self, user_id: int, order_number: str, product_name: str, amount: str) -> bool:
        """Send order confirmation to user."""
        message = (
            f"✅ <b>Order Confirmed</b>\n\n"
            f"Order Number: <code>{order_number}</code>\n"
            f"Product: {product_name}\n"
            f"Amount: {amount}\n\n"
            f"Thank you for your purchase!"
        )
        return await self.send_user_message(user_id, message)
    
    async def send_delivery_notification(self, user_id: int, delivery_message: str) -> bool:
        """Send delivery notification to user."""
        return await self.send_user_message(user_id, delivery_message)
    
    async def send_trial_activated(self, user_id: int, duration_days: int) -> bool:
        """Send trial activation notification."""
        message = (
            f"🎉 <b>Trial Activated!</b>\n\n"
            f"You have been granted a {duration_days}-day free trial.\n"
            f"Enjoy exploring our products!"
        )
        return await self.send_user_message(user_id, message)
    
    async def send_referral_reward(self, user_id: int, reward_message: str) -> bool:
        """Send referral reward notification."""
        message = f"🎁 <b>Referral Reward!</b>\n\n{reward_message}"
        return await self.send_user_message(user_id, message)