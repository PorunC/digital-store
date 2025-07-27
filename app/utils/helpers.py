"""Helper utilities."""
import hashlib
import secrets
import string
from typing import Any, Dict, Optional
from decimal import Decimal, ROUND_HALF_UP


def generate_random_string(length: int = 8, use_uppercase: bool = True, use_digits: bool = True) -> str:
    """Generate a random string."""
    chars = string.ascii_lowercase
    if use_uppercase:
        chars += string.ascii_uppercase
    if use_digits:
        chars += string.digits
    
    return ''.join(secrets.choice(chars) for _ in range(length))


def generate_order_number(prefix: str = "", length: int = 8) -> str:
    """Generate a unique order number."""
    random_part = generate_random_string(length, use_uppercase=True, use_digits=True)
    return f"{prefix}{random_part}" if prefix else random_part


def format_currency(amount: Decimal, currency: str) -> str:
    """Format currency amount."""
    # Round to 2 decimal places
    rounded_amount = amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    
    if currency == "XTR":
        return f"{rounded_amount} ⭐"
    elif currency == "RUB":
        return f"{rounded_amount} ₽"
    elif currency == "USD":
        return f"${rounded_amount}"
    elif currency == "EUR":
        return f"{rounded_amount} €"
    else:
        return f"{rounded_amount} {currency}"


def calculate_percentage(part: int, total: int, decimal_places: int = 1) -> float:
    """Calculate percentage."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimal_places)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def create_signature(data: Dict[str, Any], secret_key: str) -> str:
    """Create MD5 signature for data."""
    import json
    
    # Sort data and create string
    sorted_data = json.dumps(data, sort_keys=True, separators=(',', ':'))
    
    # Create signature with secret key
    signature_string = sorted_data + secret_key
    signature = hashlib.md5(signature_string.encode()).hexdigest()
    
    return signature


def verify_signature(data: Dict[str, Any], received_signature: str, secret_key: str) -> bool:
    """Verify signature."""
    expected_signature = create_signature(data, secret_key)
    return received_signature == expected_signature


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe filesystem operations."""
    import re
    
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing whitespace and dots
    filename = filename.strip(' .')
    
    # Limit length
    if len(filename) > 255:
        filename = filename[:255]
    
    return filename


def parse_telegram_entities(text: str, entities: Optional[list] = None) -> str:
    """Parse Telegram message entities to HTML."""
    if not entities:
        return text
    
    # Sort entities by offset in reverse order to maintain indices
    sorted_entities = sorted(entities, key=lambda x: x.offset, reverse=True)
    
    for entity in sorted_entities:
        start = entity.offset
        end = start + entity.length
        entity_text = text[start:end]
        
        if entity.type == "bold":
            replacement = f"<b>{entity_text}</b>"
        elif entity.type == "italic":
            replacement = f"<i>{entity_text}</i>"
        elif entity.type == "code":
            replacement = f"<code>{entity_text}</code>"
        elif entity.type == "pre":
            replacement = f"<pre>{entity_text}</pre>"
        elif entity.type == "url":
            replacement = f'<a href="{entity_text}">{entity_text}</a>'
        elif entity.type == "text_link":
            replacement = f'<a href="{entity.url}">{entity_text}</a>'
        else:
            continue  # Unsupported entity type
        
        text = text[:start] + replacement + text[end:]
    
    return text


def escape_html(text: str) -> str:
    """Escape HTML special characters."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format."""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"


def get_user_display_name(username: Optional[str], first_name: Optional[str], 
                         last_name: Optional[str], user_id: int) -> str:
    """Get display name for user."""
    if username:
        return f"@{username}"
    elif first_name:
        name = first_name
        if last_name:
            name += f" {last_name}"
        return name
    else:
        return f"User#{user_id}"