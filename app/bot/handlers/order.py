"""Order management handlers."""
import logging
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, LabeledPrice, PreCheckoutQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram.enums import ParseMode

from app.bot.keyboards import (
    orders_keyboard, order_detail_keyboard, payment_keyboard,
    back_keyboard
)
from app.services.order_service import OrderService
from app.services.payment_service import PaymentService
from app.services.notification_service import NotificationService
from app.schemas.order import PaymentRequest

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle my orders callback."""
    await show_user_orders(callback.message, db_user, edit=True)
    await callback.answer()


async def show_user_orders(message: Message, db_user: Any = None, edit: bool = False) -> None:
    """Show user orders."""
    try:
        if not db_user:
            # This shouldn't happen with middleware, but just in case
            text = "❌ Please start the bot first with /start"
            if edit:
                await message.edit_text(text)
            else:
                await message.answer(text)
            return
        
        orders = await OrderService.get_user_orders(db_user.id, limit=20)
        
        if not orders:
            text = (
                "📦 <b>Your Orders</b>\n\n"
                "You haven't made any orders yet.\n"
                "Visit our catalog to start shopping!"
            )
            keyboard = back_keyboard("catalog")
        else:
            # Convert to dict format
            orders_data = []
            for order in orders:
                orders_data.append({
                    'id': order.id,
                    'order_number': order.order_number,
                    'status': order.status,
                    'formatted_total': order.formatted_total
                })
            
            text = f"📦 <b>Your Orders</b>\n\nTotal orders: {len(orders)}"
            keyboard = orders_keyboard(orders_data)
        
        if edit:
            await message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        else:
            await message.answer(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
            
    except Exception as e:
        logger.error(f"Error showing user orders: {e}")
        error_text = "❌ Failed to load orders. Please try again."
        
        if edit:
            await message.edit_text(error_text, reply_markup=back_keyboard("main_menu"))
        else:
            await message.answer(error_text)


@router.callback_query(F.data.startswith("order:"))
async def order_detail_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle order detail callback."""
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order = await OrderService.get_by_id(order_id)
        
        if not order or order.user_id != db_user.id:
            await callback.answer("❌ Order not found.", show_alert=True)
            return
        
        # Get product info
        from app.services.product_service import ProductService
        product = await ProductService.get_by_id(order.product_id)
        
        # Format order details
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'completed': '✅',
            'cancelled': '❌',
            'failed': '💥'
        }.get(order.status, '❓')
        
        text_parts = [
            f"📦 <b>Order Details</b>\n",
            f"🔢 Order: <code>{order.order_number}</code>",
            f"📦 Product: {product.name if product else 'Unknown'}",
            f"💰 Amount: {order.formatted_total}",
            f"📊 Status: {status_emoji} {order.status.title()}",
            f"📅 Created: {order.created_at.strftime('%Y-%m-%d %H:%M')}",
        ]
        
        if order.expires_at and order.is_pending:
            text_parts.append(f"⏰ Expires: {order.expires_at.strftime('%Y-%m-%d %H:%M')}")
        
        if order.delivered_at:
            text_parts.append(f"✅ Delivered: {order.delivered_at.strftime('%Y-%m-%d %H:%M')}")
        
        if order.delivery_message:
            text_parts.append(f"\n📝 <b>Delivery Info:</b>\n{order.delivery_message}")
        
        text = "\n".join(text_parts)
        
        await callback.message.edit_text(
            text,
            reply_markup=order_detail_keyboard(order.id, order.status),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing order detail: {e}")
        await callback.answer("❌ Failed to load order details.")


@router.callback_query(F.data.startswith("pay_order:"))
async def pay_order_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle pay order callback."""
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order = await OrderService.get_by_id(order_id)
        
        if not order or order.user_id != db_user.id or not order.is_pending:
            await callback.answer("❌ Invalid order for payment.", show_alert=True)
            return
        
        text = (
            f"💳 <b>Payment Options</b>\n\n"
            f"Order: <code>{order.order_number}</code>\n"
            f"Amount: {order.formatted_total}\n\n"
            f"Choose your payment method:"
        )
        
        await callback.message.edit_text(
            text,
            reply_markup=payment_keyboard(order.id),
            parse_mode=ParseMode.HTML
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing payment options: {e}")
        await callback.answer("❌ Failed to load payment options.")


@router.callback_query(F.data.startswith("pay:stars:"))
async def pay_stars_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle Telegram Stars payment."""
    try:
        order_id = int(callback.data.split(":", 2)[2])
        order = await OrderService.get_by_id(order_id)
        
        if not order or order.user_id != db_user.id or not order.is_pending:
            await callback.answer("❌ Invalid order for payment.", show_alert=True)
            return
        
        # Get product for invoice
        from app.services.product_service import ProductService
        product = await ProductService.get_by_id(order.product_id)
        
        if not product:
            await callback.answer("❌ Product not found.", show_alert=True)
            return
        
        # Create Telegram Stars invoice
        prices = [LabeledPrice(label=product.name, amount=int(order.total_price))]
        
        await callback.bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Order #{order.order_number}",
            description=f"Purchase: {product.name}",
            payload=f"order_{order.id}",
            provider_token="",  # Empty for Telegram Stars
            currency="XTR",
            prices=prices
        )
        
        await callback.answer("📋 Invoice sent! Please complete the payment.")
        
    except Exception as e:
        logger.error(f"Error creating Stars payment: {e}")
        await callback.answer("❌ Failed to create payment.")


@router.callback_query(F.data.startswith("pay:crypto:"))
async def pay_crypto_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle cryptocurrency payment."""
    try:
        order_id = int(callback.data.split(":", 2)[2])
        order = await OrderService.get_by_id(order_id)
        
        if not order or order.user_id != db_user.id or not order.is_pending:
            await callback.answer("❌ Invalid order for payment.", show_alert=True)
            return
        
        # Create payment request
        payment_request = PaymentRequest(
            order_id=order.id,
            payment_gateway="cryptomus"
        )
        
        payment_response = await PaymentService.create_payment(payment_request)
        
        if not payment_response:
            await callback.answer("❌ Failed to create payment. Please try again.", show_alert=True)
            return
        
        text = (
            f"💰 <b>Cryptocurrency Payment</b>\n\n"
            f"Order: <code>{order.order_number}</code>\n"
            f"Amount: {order.formatted_total}\n\n"
            f"Click the button below to complete payment:"
        )
        
        from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Pay Now", url=payment_response.payment_url)],
            [InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_order:{order.id}")],
        ])
        
        await callback.message.edit_text(text, reply_markup=keyboard, parse_mode=ParseMode.HTML)
        await callback.answer("Payment link created!")
        
    except Exception as e:
        logger.error(f"Error creating crypto payment: {e}")
        await callback.answer("❌ Failed to create payment.")


@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle cancel order callback."""
    try:
        order_id = int(callback.data.split(":", 1)[1])
        order = await OrderService.get_by_id(order_id)
        
        if not order or order.user_id != db_user.id:
            await callback.answer("❌ Order not found.", show_alert=True)
            return
        
        if not order.is_pending:
            await callback.answer("❌ Only pending orders can be cancelled.", show_alert=True)
            return
        
        success = await OrderService.cancel_order(order.id, "Cancelled by user")
        
        if success:
            text = (
                f"❌ <b>Order Cancelled</b>\n\n"
                f"Order <code>{order.order_number}</code> has been cancelled.\n"
                f"You can create a new order anytime from our catalog."
            )
            
            await callback.message.edit_text(
                text,
                reply_markup=back_keyboard("catalog"),
                parse_mode=ParseMode.HTML
            )
            await callback.answer("Order cancelled successfully.")
        else:
            await callback.answer("❌ Failed to cancel order.", show_alert=True)
            
    except Exception as e:
        logger.error(f"Error cancelling order: {e}")
        await callback.answer("❌ Failed to cancel order.")


@router.pre_checkout_query()
async def pre_checkout_handler(pre_checkout_query: PreCheckoutQuery) -> None:
    """Handle pre-checkout for Telegram Stars payments."""
    try:
        # Extract order ID from payload
        payload = pre_checkout_query.invoice_payload
        if not payload.startswith("order_"):
            await pre_checkout_query.answer(ok=False, error_message="Invalid order")
            return
        
        order_id = int(payload.replace("order_", ""))
        order = await OrderService.get_by_id(order_id)
        
        if not order or not order.is_pending:
            await pre_checkout_query.answer(ok=False, error_message="Order not available")
            return
        
        # Check if order amount matches
        expected_amount = int(order.total_price)
        if pre_checkout_query.total_amount != expected_amount:
            await pre_checkout_query.answer(ok=False, error_message="Amount mismatch")
            return
        
        await pre_checkout_query.answer(ok=True)
        
    except Exception as e:
        logger.error(f"Error in pre-checkout: {e}")
        await pre_checkout_query.answer(ok=False, error_message="Payment processing error")


@router.message(F.successful_payment)
async def successful_payment_handler(message: Message, db_user: Any) -> None:
    """Handle successful Telegram Stars payment."""
    try:
        payment = message.successful_payment
        payload = payment.invoice_payload
        
        if not payload.startswith("order_"):
            logger.error(f"Invalid payment payload: {payload}")
            return
        
        order_id = int(payload.replace("order_", ""))
        order = await OrderService.get_by_id(order_id)
        
        if not order:
            logger.error(f"Order not found for payment: {order_id}")
            return
        
        # Complete the order
        success = await OrderService.complete_order(order.id)
        
        if success:
            # Generate delivery message
            delivery_message = await OrderService.generate_delivery_message(order)
            
            if delivery_message:
                await message.answer(delivery_message)
            else:
                await message.answer(
                    f"✅ <b>Payment Successful!</b>\n\n"
                    f"Order <code>{order.order_number}</code> has been completed.\n"
                    f"Thank you for your purchase!"
                )
            
            # Notify admins
            from app.services.product_service import ProductService
            product = await ProductService.get_by_id(order.product_id)
            
            # This would need to be initialized with bot instance
            # notification_service = NotificationService(message.bot)
            # await notification_service.notify_order_completed(
            #     order.order_number, 
            #     db_user.telegram_id,
            #     product.name if product else "Unknown"
            # )
        else:
            await message.answer(
                "❌ Payment received but order processing failed. "
                "Please contact support."
            )
            
    except Exception as e:
        logger.error(f"Error processing successful payment: {e}")
        await message.answer(
            "❌ Payment processing error. Please contact support if you were charged."
        )