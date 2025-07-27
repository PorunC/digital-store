"""Order model."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict, Optional

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderStatus(str, Enum):
    """Order status types."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentGateway(str, Enum):
    """Supported payment gateways."""
    TELEGRAM_STARS = "telegram_stars"
    CRYPTOMUS = "cryptomus"


class Order(Base):
    """Order model for purchases."""
    
    __tablename__ = "orders"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Order identification
    order_number: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    
    # Foreign keys
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    
    # Order details
    quantity: Mapped[int] = mapped_column(default=1)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False)
    
    # Status and payment
    status: Mapped[str] = mapped_column(String(20), default=OrderStatus.PENDING.value, index=True)
    payment_gateway: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    payment_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    
    # Delivery
    delivery_data: Mapped[Optional[Dict]] = mapped_column(JSON, nullable=True)
    delivery_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    delivered_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Trial and referral info
    is_trial: Mapped[bool] = mapped_column(default=False)
    referral_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
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
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="orders")
    product: Mapped["Product"] = relationship("Product", back_populates="orders")
    
    def __repr__(self) -> str:
        return f"<Order(id={self.id}, order_number={self.order_number}, status={self.status})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if order is pending."""
        return self.status == OrderStatus.PENDING.value
    
    @property
    def is_completed(self) -> bool:
        """Check if order is completed."""
        return self.status == OrderStatus.COMPLETED.value
    
    @property
    def is_cancelled(self) -> bool:
        """Check if order is cancelled."""
        return self.status == OrderStatus.CANCELLED.value
    
    @property
    def is_expired(self) -> bool:
        """Check if order is expired."""
        if not self.expires_at:
            return False
        return datetime.now() > self.expires_at
    
    @property
    def formatted_total(self) -> str:
        """Get formatted total price."""
        if self.currency == "XTR":
            return f"{self.total_price} ⭐"
        elif self.currency == "RUB":
            return f"{self.total_price} ₽"
        elif self.currency == "USD":
            return f"${self.total_price}"
        elif self.currency == "EUR":
            return f"{self.total_price} €"
        else:
            return f"{self.total_price} {self.currency}"
    
    def mark_as_completed(self) -> None:
        """Mark order as completed."""
        self.status = OrderStatus.COMPLETED.value
        self.delivered_at = datetime.now()
    
    def mark_as_cancelled(self) -> None:
        """Mark order as cancelled."""
        self.status = OrderStatus.CANCELLED.value