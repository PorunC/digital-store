"""Catalog and product handlers."""
import logging
from typing import Any

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.bot.keyboards import (
    catalog_keyboard, products_keyboard, product_detail_keyboard,
    payment_keyboard, back_keyboard
)
from app.services.product_service import ProductService
from app.services.order_service import OrderService
from app.schemas.order import OrderCreate

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data == "catalog")
async def catalog_callback(callback: CallbackQuery) -> None:
    """Handle catalog callback."""
    await show_catalog(callback.message, edit=True)
    await callback.answer()


async def show_catalog(message: Message, edit: bool = False) -> None:
    """Show product catalog."""
    try:
        # Get available categories
        categories = await ProductService.get_categories()
        
        text = (
            f"🛍️ <b>Product Catalog</b>\n\n"
            f"Choose a category to browse our digital products:\n"
            f"💎 High-quality digital goods\n"
            f"⚡ Instant delivery\n"
            f"🔒 Secure transactions"
        )
        
        keyboard = catalog_keyboard(categories)
        
        if edit and message:
            await message.edit_text(text, reply_markup=keyboard)
        else:
            await message.answer(text, reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error showing catalog: {e}")
        error_text = "❌ Failed to load catalog. Please try again."
        
        if edit and message:
            await message.edit_text(error_text, reply_markup=back_keyboard("main_menu"))
        else:
            await message.answer(error_text)


@router.callback_query(F.data == "featured")
async def featured_callback(callback: CallbackQuery) -> None:
    """Handle featured products callback."""
    try:
        products = await ProductService.get_featured_products()
        
        if not products:
            await callback.message.edit_text(
                "📦 No featured products available at the moment.",
                reply_markup=back_keyboard("catalog")
            )
            await callback.answer()
            return
        
        # Convert to dict format for keyboard
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'name': product.name,
                'formatted_price': product.formatted_price
            })
        
        text = f"⭐ <b>Featured Products</b>\n\nOur most popular items:"
        
        await callback.message.edit_text(
            text,
            reply_markup=products_keyboard(products_data, "featured")
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing featured products: {e}")
        await callback.answer("❌ Failed to load featured products.")


@router.callback_query(F.data.startswith("category:"))
async def category_callback(callback: CallbackQuery) -> None:
    """Handle category selection callback."""
    try:
        category = callback.data.split(":", 1)[1]
        await show_category_products(callback, category)
        
    except Exception as e:
        logger.error(f"Error showing category products: {e}")
        await callback.answer("❌ Failed to load products.")


@router.callback_query(F.data.startswith("products:"))
async def products_page_callback(callback: CallbackQuery) -> None:
    """Handle products pagination callback."""
    try:
        _, category, page_str = callback.data.split(":")
        page = int(page_str)
        await show_category_products(callback, category, page)
        
    except Exception as e:
        logger.error(f"Error showing products page: {e}")
        await callback.answer("❌ Failed to load products.")


async def show_category_products(callback: CallbackQuery, category: str, page: int = 0) -> None:
    """Show products in a category."""
    products = await ProductService.get_available_products(category=category)
    
    if not products:
        await callback.message.edit_text(
            f"📦 No products available in {category.title()} category.",
            reply_markup=back_keyboard("catalog")
        )
        await callback.answer()
        return
    
    # Convert to dict format
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'formatted_price': product.formatted_price
        })
    
    emoji = {
        'software': '💻',
        'gaming': '🎮', 
        'subscription': '📺',
        'digital': '💎',
        'education': '📚'
    }.get(category, '📦')
    
    text = f"{emoji} <b>{category.title()} Products</b>\n\nSelect a product to view details:"
    
    await callback.message.edit_text(
        text,
        reply_markup=products_keyboard(products_data, category, page)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("product:"))
async def product_detail_callback(callback: CallbackQuery) -> None:
    """Handle product detail callback."""
    try:
        product_id = int(callback.data.split(":", 1)[1])
        product = await ProductService.get_by_id(product_id)
        
        if not product:
            await callback.answer("❌ Product not found.", show_alert=True)
            return
        
        # Build product description
        description_parts = [
            f"💎 <b>{product.name}</b>\n",
            f"💰 Price: <b>{product.formatted_price}</b>",
            f"📦 Category: {product.category.title()}",
        ]
        
        if product.description:
            description_parts.append(f"\n📝 {product.description}")
        
        if product.duration_days:
            if product.duration_days == 0:
                description_parts.append("⏰ Duration: Permanent")
            else:
                description_parts.append(f"⏰ Duration: {product.duration_days} days")
        
        # Stock info
        if product.stock_count is not None:
            description_parts.append(f"📊 Stock: {product.stock_count} available")
        else:
            description_parts.append("📊 Stock: Unlimited")
        
        text = "\n".join(description_parts)
        
        await callback.message.edit_text(
            text,
            reply_markup=product_detail_keyboard(product.id, product.is_available)
        )
        await callback.answer()
        
    except Exception as e:
        logger.error(f"Error showing product detail: {e}")
        await callback.answer("❌ Failed to load product details.")


@router.callback_query(F.data.startswith("buy:"))
async def buy_product_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle buy product callback."""
    try:
        product_id = int(callback.data.split(":", 1)[1])
        await create_order(callback, db_user, product_id, "cryptomus")
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        await callback.answer("❌ Failed to create order.")


@router.callback_query(F.data.startswith("buy_stars:"))
async def buy_stars_callback(callback: CallbackQuery, db_user: Any) -> None:
    """Handle buy with stars callback."""
    try:
        product_id = int(callback.data.split(":", 1)[1])
        await create_order(callback, db_user, product_id, "telegram_stars")
        
    except Exception as e:
        logger.error(f"Error creating stars order: {e}")
        await callback.answer("❌ Failed to create order.")


async def create_order(callback: CallbackQuery, db_user: Any, product_id: int, gateway: str) -> None:
    """Create order for product."""
    # Check if product is available
    product = await ProductService.get_by_id(product_id)
    if not product or not product.is_available:
        await callback.answer("❌ Product is not available.", show_alert=True)
        return
    
    # Create order
    order_data = OrderCreate(
        product_id=product_id,
        payment_gateway=gateway,
        quantity=1
    )
    
    order = await OrderService.create_order(db_user.id, order_data)
    
    if not order:
        await callback.answer("❌ Failed to create order. Please try again.", show_alert=True)
        return
    
    # Show payment options
    text = (
        f"🛒 <b>Order Created</b>\n\n"
        f"📦 Product: {product.name}\n"
        f"💰 Amount: {order.formatted_total}\n"
        f"🔢 Order: <code>{order.order_number}</code>\n\n"
        f"⏰ This order will expire in 15 minutes.\n"
        f"Please select your payment method:"
    )
    
    await callback.message.edit_text(
        text,
        reply_markup=payment_keyboard(order.id)
    )
    await callback.answer("Order created successfully!")