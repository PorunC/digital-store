"""Admin panel handlers."""
import logging
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from app.bot.keyboards import admin_keyboard, back_keyboard, confirmation_keyboard
from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.services.order_service import OrderService

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("admin"))
async def admin_command(message: Message, is_admin: bool) -> None:
    """Handle /admin command."""
    if not is_admin:
        await message.answer("❌ You don't have admin permissions.")
        return
    
    await show_admin_panel(message)


@router.callback_query(F.data == "admin")
async def admin_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin callback."""
    if not is_admin:
        await callback.answer("❌ You don't have admin permissions.", show_alert=True)
        return
    
    await show_admin_panel(callback.message, edit=True)
    await callback.answer()


async def show_admin_panel(message: Message, edit: bool = False) -> None:
    """Show admin panel."""
    text = (
        f"🔧 <b>Admin Panel</b>\n\n"
        f"Welcome to the administration panel.\n"
        f"Use the buttons below to manage the bot:"
    )
    
    keyboard = admin_keyboard()
    
    if edit:
        await message.edit_text(text, reply_markup=keyboard)
    else:
        await message.answer(text, reply_markup=keyboard)


@router.callback_query(F.data == "admin:stats")
async def admin_stats_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin statistics callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        # Get statistics from all services
        user_stats = await UserService.get_user_stats()
        product_stats = await ProductService.get_product_stats()
        order_stats = await OrderService.get_order_stats()
        
        text = (
            f"📊 <b>Bot Statistics</b>\n\n"
            f"👥 <b>Users:</b>\n"
            f"• Total: {user_stats.total_users}\n"
            f"• Active: {user_stats.active_users}\n" 
            f"• Trial users: {user_stats.trial_users}\n"
            f"• Admins: {user_stats.admin_users}\n"
            f"• New today: {user_stats.new_users_today}\n\n"
            f"📦 <b>Products:</b>\n"
            f"• Total: {product_stats.total_products}\n"
            f"• Active: {product_stats.active_products}\n"
            f"• Out of stock: {product_stats.out_of_stock}\n"
            f"• Total sales: {product_stats.total_sales}\n\n"
            f"🛒 <b>Orders:</b>\n"
            f"• Total: {order_stats.total_orders}\n"
            f"• Pending: {order_stats.pending_orders}\n"
            f"• Completed: {order_stats.completed_orders}\n"
            f"• Cancelled: {order_stats.cancelled_orders}\n"
            f"• Revenue today: {order_stats.revenue_today}\n"
            f"• Total revenue: {order_stats.revenue_total}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("admin")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await callback.answer("❌ Failed to load statistics.")


@router.callback_query(F.data == "admin:users")
async def admin_users_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin users callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        user_stats = await UserService.get_user_stats()
        
        text = (
            f"👥 <b>User Management</b>\n\n"
            f"📊 <b>Statistics:</b>\n"
            f"• Total users: {user_stats.total_users}\n"
            f"• Active users: {user_stats.active_users}\n"
            f"• Trial users: {user_stats.trial_users}\n"
            f"• New today: {user_stats.new_users_today}\n\n"
            f"🔧 <b>Actions:</b>\n"
            f"Use /find_user [telegram_id] to find specific user\n"
            f"Use /ban_user [telegram_id] to ban user\n"
            f"Use /unban_user [telegram_id] to unban user"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("admin")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing admin users: {e}")
        await callback.answer("❌ Failed to load user management.")


@router.callback_query(F.data == "admin:products")
async def admin_products_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin products callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        product_stats = await ProductService.get_product_stats()
        
        text = (
            f"📦 <b>Product Management</b>\n\n"
            f"📊 <b>Statistics:</b>\n"
            f"• Total products: {product_stats.total_products}\n"
            f"• Active products: {product_stats.active_products}\n"
            f"• Out of stock: {product_stats.out_of_stock}\n"
            f"• Total sales: {product_stats.total_sales}\n\n"
            f"🔧 <b>Actions:</b>\n"
            f"• Load products from JSON file\n"
            f"• Export products to JSON file\n"
            f"• View product details\n\n"
            f"Use the buttons below to manage products:"
        )
        
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📥 Load from JSON", callback_data="admin:load_products")],
            [InlineKeyboardButton(text="📤 Export to JSON", callback_data="admin:export_products")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin")],
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing admin products: {e}")
        await callback.answer("❌ Failed to load product management.")


@router.callback_query(F.data == "admin:orders")
async def admin_orders_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin orders callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        order_stats = await OrderService.get_order_stats()
        
        text = (
            f"🛒 <b>Order Management</b>\n\n"
            f"📊 <b>Statistics:</b>\n"
            f"• Total orders: {order_stats.total_orders}\n"
            f"• Pending: {order_stats.pending_orders}\n"
            f"• Completed: {order_stats.completed_orders}\n"
            f"• Cancelled: {order_stats.cancelled_orders}\n"
            f"• Revenue today: {order_stats.revenue_today}\n"
            f"• Total revenue: {order_stats.revenue_total}\n\n"
            f"🔧 <b>Actions:</b>\n"
            f"• Clean up expired orders\n"
            f"• View recent orders\n"
            f"• Export order data"
        )
        
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🧹 Clean Expired", callback_data="admin:cleanup_orders")],
            [InlineKeyboardButton(text="📋 Recent Orders", callback_data="admin:recent_orders")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="admin")],
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard)
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing admin orders: {e}")
        await callback.answer("❌ Failed to load order management.")


@router.callback_query(F.data == "admin:load_products")
async def admin_load_products_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle load products callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        loaded_count = await ProductService.load_products_from_json()
        
        text = f"📥 <b>Products Loaded</b>\n\nSuccessfully loaded {loaded_count} products from JSON file."
        
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("admin:products")
        )
        await callback.answer(f"Loaded {loaded_count} products!")
        
    except Exception as e:
        logger.error(f"Error loading products: {e}")
        await callback.answer("❌ Failed to load products.")


@router.callback_query(F.data == "admin:export_products")
async def admin_export_products_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle export products callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        success = await ProductService.export_products_to_json()
        
        if success:
            text = "📤 <b>Products Exported</b>\n\nProducts have been successfully exported to JSON file."
            await callback.answer("Products exported successfully!")
        else:
            text = "❌ <b>Export Failed</b>\n\nFailed to export products. Please check the logs."
            await callback.answer("Export failed!", show_alert=True)
        
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("admin:products")
        )
        
    except Exception as e:
        logger.error(f"Error exporting products: {e}")
        await callback.answer("❌ Failed to export products.")


@router.callback_query(F.data == "admin:cleanup_orders")
async def admin_cleanup_orders_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle cleanup orders callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    try:
        expired_count = await OrderService.expire_pending_orders()
        
        text = f"🧹 <b>Orders Cleaned</b>\n\nExpired {expired_count} pending orders."
        
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("admin:orders")
        )
        await callback.answer(f"Cleaned {expired_count} expired orders!")
        
    except Exception as e:
        logger.error(f"Error cleaning orders: {e}")
        await callback.answer("❌ Failed to clean orders.")


@router.callback_query(F.data == "admin:broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin broadcast callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    text = (
        f"📢 <b>Broadcast Message</b>\n\n"
        f"To send a broadcast message to all users:\n"
        f"1. Use command /broadcast [message]\n"
        f"2. Confirm the broadcast\n"
        f"3. Message will be sent to all active users\n\n"
        f"⚠️ Use this feature responsibly!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("admin")
    )
    await callback.answer()


@router.callback_query(F.data == "admin:settings")
async def admin_settings_callback(callback: CallbackQuery, is_admin: bool) -> None:
    """Handle admin settings callback."""
    if not is_admin:
        await callback.answer("❌ Access denied.", show_alert=True)
        return
    
    from app.config import settings
    
    text = (
        f"⚙️ <b>Bot Settings</b>\n\n"
        f"🌍 Environment: {settings.environment}\n"
        f"💎 Trial enabled: {'✅' if settings.trial_enabled else '❌'}\n"
        f"📅 Trial duration: {settings.trial_duration_days} days\n"
        f"👥 Referral enabled: {'✅' if settings.referral_enabled else '❌'}\n"
        f"🎁 Referral reward: {settings.referral_reward_days} days\n"
        f"⭐ Telegram Stars: {'✅' if settings.telegram_stars_enabled else '❌'}\n"
        f"💰 Cryptomus: {'✅' if settings.cryptomus_enabled else '❌'}\n"
        f"💵 Default currency: {settings.default_currency}\n\n"
        f"Settings can be changed in the configuration file."
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("admin")
    )
    await callback.answer()


# Admin commands
@router.message(Command("find_user"))
async def find_user_command(message: Message, is_admin: bool) -> None:
    """Handle find user command."""
    if not is_admin:
        await message.answer("❌ You don't have admin permissions.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Usage: /find_user [telegram_id]")
            return
        
        telegram_id = int(args[1])
        user = await UserService.get_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"❌ User {telegram_id} not found.")
            return
        
        text = (
            f"👤 <b>User Information</b>\n\n"
            f"🆔 ID: <code>{user.telegram_id}</code>\n"
            f"👤 Name: {user.display_name}\n"
            f"📅 Joined: {user.created_at.strftime('%Y-%m-%d')}\n"
            f"📱 Last activity: {user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else 'Never'}\n"
            f"🟢 Active: {'✅' if user.is_active else '❌'}\n"
            f"🚫 Banned: {'✅' if user.is_banned else '❌'}\n"
            f"👑 Admin: {'✅' if user.is_admin else '❌'}\n"
            f"💎 Trial used: {'✅' if user.trial_used else '❌'}\n"
            f"👥 Referrals: {user.total_referred}"
        )
        
        await message.answer(text)
        
    except ValueError:
        await message.answer("❌ Invalid telegram ID.")
    except Exception as e:
        logger.error(f"Error finding user: {e}")
        await message.answer("❌ Error finding user.")


@router.message(Command("ban_user"))
async def ban_user_command(message: Message, is_admin: bool) -> None:
    """Handle ban user command."""
    if not is_admin:
        await message.answer("❌ You don't have admin permissions.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Usage: /ban_user [telegram_id]")
            return
        
        telegram_id = int(args[1])
        user = await UserService.get_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"❌ User {telegram_id} not found.")
            return
        
        success = await UserService.ban_user(user.id, ban=True)
        
        if success:
            await message.answer(f"✅ User {telegram_id} has been banned.")
        else:
            await message.answer(f"❌ Failed to ban user {telegram_id}.")
            
    except ValueError:
        await message.answer("❌ Invalid telegram ID.")
    except Exception as e:
        logger.error(f"Error banning user: {e}")
        await message.answer("❌ Error banning user.")


@router.message(Command("unban_user"))
async def unban_user_command(message: Message, is_admin: bool) -> None:
    """Handle unban user command."""
    if not is_admin:
        await message.answer("❌ You don't have admin permissions.")
        return
    
    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer("Usage: /unban_user [telegram_id]")
            return
        
        telegram_id = int(args[1])
        user = await UserService.get_by_telegram_id(telegram_id)
        
        if not user:
            await message.answer(f"❌ User {telegram_id} not found.")
            return
        
        success = await UserService.ban_user(user.id, ban=False)
        
        if success:
            await message.answer(f"✅ User {telegram_id} has been unbanned.")
        else:
            await message.answer(f"❌ Failed to unban user {telegram_id}.")
            
    except ValueError:
        await message.answer("❌ Invalid telegram ID.")
    except Exception as e:
        logger.error(f"Error unbanning user: {e}")
        await message.answer("❌ Error unbanning user.")