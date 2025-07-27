"""Start and main menu handlers."""
import logging
from typing import Dict, Any

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from app.bot.keyboards import main_menu_keyboard, profile_keyboard
from app.services.user_service import UserService
from app.config import settings

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("start"))
async def start_command(message: Message, db_user: Any, state: FSMContext) -> None:
    """Handle /start command."""
    await state.clear()
    
    welcome_text = (
        f"👋 Welcome to our Digital Store, {db_user.display_name}!\n\n"
        f"🛍️ Browse our catalog of digital products\n"
        f"💎 Get free trial access\n"
        f"👥 Earn rewards through referrals\n\n"
        f"Choose an option from the menu below:"
    )
    
    await message.answer(
        welcome_text,
        reply_markup=main_menu_keyboard()
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery, db_user: Any, state: FSMContext) -> None:
    """Handle main menu callback."""
    await state.clear()
    
    text = (
        f"🏠 *Main Menu*\n\n"
        f"Welcome back, {db_user.display_name}!\n"
        f"What would you like to do?"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle profile callback."""
    # Get user statistics
    trial_info = ""
    if db_user.trial_used:
        if db_user.has_active_trial:
            trial_info = f"🟢 Active until {db_user.trial_end.strftime('%Y-%m-%d')}"
        else:
            trial_info = "🔴 Used"
    else:
        trial_info = "🟡 Available"
    
    text = (
        f"👤 *Your Profile*\n\n"
        f"🆔 ID: `{db_user.telegram_id}`\n"
        f"👤 Name: {db_user.display_name}\n"
        f"📅 Joined: {db_user.created_at.strftime('%Y-%m-%d')}\n"
        f"💎 Trial: {trial_info}\n"
        f"👥 Referrals: {db_user.total_referred}\n"
        f"🔗 Your referral code: `{db_user.referral_code}`"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=profile_keyboard(has_trial=db_user.trial_used)
    )
    await callback.answer()


@router.callback_query(F.data == "activate_trial")
async def activate_trial_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle trial activation."""
    if db_user.trial_used:
        await callback.answer("❌ You have already used your free trial!", show_alert=True)
        return
    
    if not settings.trial_enabled:
        await callback.answer("❌ Trial system is currently disabled.", show_alert=True)
        return
    
    success = await UserService.activate_trial(db_user.id)
    
    if success:
        text = (
            f"🎉 *Trial Activated!*\n\n"
            f"✅ Your {settings.trial_duration_days}-day free trial is now active!\n"
            f"🛍️ Browse our catalog and enjoy premium access.\n\n"
            f"Trial expires: {db_user.trial_end.strftime('%Y-%m-%d %H:%M') if db_user.trial_end else 'N/A'}"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=profile_keyboard(has_trial=True)
        )
        await callback.answer("🎉 Trial activated successfully!")
    else:
        await callback.answer("❌ Failed to activate trial. Please try again.", show_alert=True)


@router.callback_query(F.data == "referral")
async def referral_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle referral information."""
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={db_user.referral_code}"
    
    text = (
        f"👥 *Referral Program*\n\n"
        f"🎁 Invite friends and earn rewards!\n\n"
        f"🔗 Your referral link:\n"
        f"`{referral_link}`\n\n"
        f"📊 Your statistics:\n"
        f"👥 Total referrals: {db_user.total_referred}\n\n"
        f"💡 Share your link with friends to earn rewards when they make purchases!"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=profile_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery) -> None:
    """Handle support information."""
    text = (
        f"ℹ️ *Support & Information*\n\n"
        f"🆘 Need help? Contact our support team:\n"
        f"📧 Email: support@digitalstore.com\n"
        f"💬 Telegram: @support\n\n"
        f"📋 *How to use the bot:*\n"
        f"1️⃣ Browse the catalog\n"
        f"2️⃣ Select a product\n"
        f"3️⃣ Complete payment\n"
        f"4️⃣ Receive your digital product\n\n"
        f"💎 Don't forget to try our free trial!"
    )
    
    from app.bot.keyboards import back_keyboard
    await callback.message.edit_text(
        text,
        reply_markup=back_keyboard("main_menu")
    )
    await callback.answer()


@router.callback_query(F.data == "profile_stats")
async def profile_stats_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle profile statistics callback."""
    try:
        from app.services.order_service import OrderService
        
        # Get user order statistics
        order_stats = await OrderService.get_user_order_stats(db_user.id)
        
        text = (
            f"📊 *Your Statistics*\n\n"
            f"👤 *Account Info:*\n"
            f"📅 Member since: {db_user.created_at.strftime('%Y-%m-%d')}\n"
            f"🎯 Trial used: {'Yes' if db_user.trial_used else 'No'}\n"
            f"🔗 Referral code: `{db_user.referral_code}`\n"
            f"👥 Referrals: {db_user.total_referred}\n\n"
            f"🛒 *Order Statistics:*\n"
            f"📦 Total orders: {order_stats.get('total_orders', 0)}\n"
            f"✅ Completed: {order_stats.get('completed_orders', 0)}\n"
            f"⏳ Pending: {order_stats.get('pending_orders', 0)}\n"
            f"💰 Total spent: {order_stats.get('total_spent', 0)} {settings.default_currency.value}\n\n"
            f"🏆 Keep shopping to unlock more rewards!"
        )
        
        from app.bot.keyboards import back_keyboard
        await callback.message.edit_text(
            text,
            reply_markup=back_keyboard("profile")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Failed to get user statistics: {e}")
        await callback.answer("❌ Failed to load statistics. Please try again.", show_alert=True)


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    """Handle /help command."""
    text = (
        f"🆘 *Help & Commands*\n\n"
        f"*Available commands:*\n"
        f"/start - Start the bot\n"
        f"/help - Show this help message\n"
        f"/catalog - Browse products\n"
        f"/profile - View your profile\n"
        f"/orders - View your orders\n\n"
        f"Use the inline buttons to navigate through the bot!"
    )
    
    await message.answer(text)


@router.message(Command("catalog"))
async def catalog_command(message: Message) -> None:
    """Handle /catalog command."""
    from app.bot.handlers.catalog import show_catalog
    await show_catalog(message)


@router.message(Command("profile"))
async def profile_command(message: Message, db_user: Any) -> None:
    """Handle /profile command."""
    await profile_callback(
        type('CallbackQuery', (), {
            'message': message,
            'answer': lambda *args, **kwargs: None
        })(),
        db_user
    )


@router.message(Command("orders"))
async def orders_command(message: Message) -> None:
    """Handle /orders command."""
    from app.bot.handlers.order import show_user_orders
    await show_user_orders(message)


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery) -> None:
    """Handle no-operation callback."""
    await callback.answer()