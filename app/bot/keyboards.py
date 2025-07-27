"""Keyboard layouts for the bot."""
from typing import List, Optional

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    buttons = [
        [InlineKeyboardButton(text="🛍️ Catalog", callback_data="catalog")],
        [InlineKeyboardButton(text="📦 My Orders", callback_data="my_orders")],
        [InlineKeyboardButton(text="👤 Profile", callback_data="profile")],
        [InlineKeyboardButton(text="💎 Try for Free", callback_data="trial")],
        [InlineKeyboardButton(text="👥 Referral", callback_data="referral")],
        [InlineKeyboardButton(text="ℹ️ Support", callback_data="support")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def catalog_keyboard(categories: List[str]) -> InlineKeyboardMarkup:
    """Create catalog categories keyboard."""
    buttons = []
    
    # Add category buttons (2 per row)
    for i in range(0, len(categories), 2):
        row = []
        for j in range(2):
            if i + j < len(categories):
                category = categories[i + j]
                emoji = get_category_emoji(category)
                row.append(InlineKeyboardButton(
                    text=f"{emoji} {category.title()}",
                    callback_data=f"category:{category}"
                ))
        buttons.append(row)
    
    # Add navigation buttons
    buttons.extend([
        [InlineKeyboardButton(text="⭐ Featured", callback_data="featured")],
        [InlineKeyboardButton(text="🔙 Back to Menu", callback_data="main_menu")],
    ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def products_keyboard(products: List[dict], category: str, page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Create products list keyboard."""
    buttons = []
    
    # Add product buttons
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(products))
    
    for product in products[start_idx:end_idx]:
        buttons.append([InlineKeyboardButton(
            text=f"💎 {product['name']} - {product['formatted_price']}",
            callback_data=f"product:{product['id']}"
        )])
    
    # Add pagination if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"products:{category}:{page-1}"))
    if end_idx < len(products):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"products:{category}:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add back button
    buttons.append([InlineKeyboardButton(text="🔙 Back to Categories", callback_data="catalog")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def product_detail_keyboard(product_id: int, is_available: bool = True) -> InlineKeyboardMarkup:
    """Create product detail keyboard."""
    buttons = []
    
    if is_available:
        buttons.extend([
            [InlineKeyboardButton(text="💰 Buy Now", callback_data=f"buy:{product_id}")],
            [InlineKeyboardButton(text="⭐ Buy with Stars", callback_data=f"buy_stars:{product_id}")],
        ])
    else:
        buttons.append([InlineKeyboardButton(text="❌ Out of Stock", callback_data="noop")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back to Products", callback_data="catalog")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_keyboard(order_id: int) -> InlineKeyboardMarkup:
    """Create payment options keyboard."""
    buttons = [
        [InlineKeyboardButton(text="⭐ Pay with Telegram Stars", callback_data=f"pay:stars:{order_id}")],
        [InlineKeyboardButton(text="💰 Pay with Crypto", callback_data=f"pay:crypto:{order_id}")],
        [InlineKeyboardButton(text="❌ Cancel Order", callback_data=f"cancel_order:{order_id}")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def orders_keyboard(orders: List[dict], page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    """Create orders list keyboard."""
    buttons = []
    
    # Add order buttons
    start_idx = page * per_page
    end_idx = min(start_idx + per_page, len(orders))
    
    for order in orders[start_idx:end_idx]:
        status_emoji = get_status_emoji(order['status'])
        buttons.append([InlineKeyboardButton(
            text=f"{status_emoji} {order['order_number']} - {order['formatted_total']}",
            callback_data=f"order:{order['id']}"
        )])
    
    # Add pagination if needed
    nav_buttons = []
    if page > 0:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Prev", callback_data=f"orders:{page-1}"))
    if end_idx < len(orders):
        nav_buttons.append(InlineKeyboardButton(text="➡️ Next", callback_data=f"orders:{page+1}"))
    
    if nav_buttons:
        buttons.append(nav_buttons)
    
    # Add back button
    buttons.append([InlineKeyboardButton(text="🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def order_detail_keyboard(order_id: int, status: str) -> InlineKeyboardMarkup:
    """Create order detail keyboard."""
    buttons = []
    
    if status == "pending":
        buttons.extend([
            [InlineKeyboardButton(text="💳 Pay Now", callback_data=f"pay_order:{order_id}")],
            [InlineKeyboardButton(text="❌ Cancel", callback_data=f"cancel_order:{order_id}")],
        ])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back to Orders", callback_data="my_orders")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_keyboard(has_trial: bool = False) -> InlineKeyboardMarkup:
    """Create profile keyboard."""
    buttons = [
        [InlineKeyboardButton(text="📊 Statistics", callback_data="profile_stats")],
        [InlineKeyboardButton(text="👥 My Referrals", callback_data="my_referrals")],
    ]
    
    if not has_trial:
        buttons.insert(0, [InlineKeyboardButton(text="💎 Activate Trial", callback_data="activate_trial")])
    
    buttons.append([InlineKeyboardButton(text="🔙 Back to Menu", callback_data="main_menu")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_keyboard() -> InlineKeyboardMarkup:
    """Create admin panel keyboard."""
    buttons = [
        [InlineKeyboardButton(text="📊 Statistics", callback_data="admin:stats")],
        [InlineKeyboardButton(text="👥 Users", callback_data="admin:users")],
        [InlineKeyboardButton(text="📦 Products", callback_data="admin:products")],
        [InlineKeyboardButton(text="🛒 Orders", callback_data="admin:orders")],
        [InlineKeyboardButton(text="📢 Broadcast", callback_data="admin:broadcast")],
        [InlineKeyboardButton(text="⚙️ Settings", callback_data="admin:settings")],
        [InlineKeyboardButton(text="🔙 Main Menu", callback_data="main_menu")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirmation_keyboard(action: str, item_id: Optional[int] = None) -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    confirm_data = f"confirm:{action}"
    cancel_data = f"cancel:{action}"
    
    if item_id:
        confirm_data += f":{item_id}"
        cancel_data += f":{item_id}"
    
    buttons = [
        [
            InlineKeyboardButton(text="✅ Confirm", callback_data=confirm_data),
            InlineKeyboardButton(text="❌ Cancel", callback_data=cancel_data),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_keyboard(callback_data: str) -> InlineKeyboardMarkup:
    """Create simple back button keyboard."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Back", callback_data=callback_data)]
    ])


def get_category_emoji(category: str) -> str:
    """Get emoji for product category."""
    emojis = {
        "software": "💻",
        "gaming": "🎮",
        "subscription": "📺",
        "digital": "💎",
        "education": "📚",
    }
    return emojis.get(category.lower(), "📦")


def get_status_emoji(status: str) -> str:
    """Get emoji for order status."""
    emojis = {
        "pending": "⏳",
        "processing": "🔄",
        "completed": "✅",
        "cancelled": "❌",
        "failed": "💥",
        "refunded": "💸",
    }
    return emojis.get(status.lower(), "❓")