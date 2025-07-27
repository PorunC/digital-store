"""Product model."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

from sqlalchemy import JSON, Boolean, DateTime, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ProductCategory(str, Enum):
    """Product categories."""
    SOFTWARE = "software"
    GAMING = "gaming"
    SUBSCRIPTION = "subscription"
    DIGITAL = "digital"
    EDUCATION = "education"


class DeliveryType(str, Enum):
    """Product delivery types."""
    LICENSE_KEY = "license_key"
    ACCOUNT_INFO = "account_info"
    DOWNLOAD_LINK = "download_link"
    API_ACCESS = "api_access"
    INSTANT = "instant"


class Product(Base):
    """Product model for digital goods."""
    
    __tablename__ = "products"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Basic info
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(50), default=ProductCategory.DIGITAL.value)
    
    # Pricing
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="RUB")
    
    # Product details
    delivery_type: Mapped[str] = mapped_column(String(50), default=DeliveryType.INSTANT.value)
    duration_days: Mapped[Optional[int]] = mapped_column(nullable=True)  # 0 for permanent
    
    # Stock management
    stock_count: Mapped[Optional[int]] = mapped_column(nullable=True)  # None for unlimited
    sold_count: Mapped[int] = mapped_column(default=0)
    
    # Delivery configuration
    delivery_config: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # SEO and display
    slug: Mapped[Optional[str]] = mapped_column(String(255), unique=True, nullable=True, index=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(default=0)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False
    )
    
    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="product")
    
    def __repr__(self) -> str:
        return f"<Product(id={self.id}, name={self.name}, price={self.price})>"
    
    @property
    def is_in_stock(self) -> bool:
        """Check if product is in stock."""
        if self.stock_count is None:  # Unlimited stock
            return True
        return self.stock_count > 0
    
    @property
    def is_available(self) -> bool:
        """Check if product is available for purchase."""
        return self.is_active and self.is_in_stock
    
    @property
    def formatted_price(self) -> str:
        """Get formatted price string."""
        if self.currency == "XTR":
            return f"{self.price} ⭐"
        elif self.currency == "RUB":
            return f"{self.price} ₽"
        elif self.currency == "USD":
            return f"${self.price}"
        elif self.currency == "EUR":
            return f"{self.price} €"
        else:
            return f"{self.price} {self.currency}"
    
    def decrease_stock(self, amount: int = 1) -> bool:
        """Decrease stock count."""
        if self.stock_count is None:  # Unlimited stock
            return True
        if self.stock_count >= amount:
            self.stock_count -= amount
            self.sold_count += amount
            return True
        return False