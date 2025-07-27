"""Order schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.models.order import OrderStatus, PaymentGateway


class OrderBase(BaseModel):
    """Base order schema."""
    quantity: int = Field(default=1, gt=0, description="Order quantity")


class OrderCreate(OrderBase):
    """Schema for creating an order."""
    product_id: int = Field(..., description="Product ID")
    payment_gateway: Optional[str] = Field(None, description="Payment gateway")
    referral_code: Optional[str] = Field(None, description="Referral code")
    is_trial: bool = Field(default=False, description="Is trial order")


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    status: Optional[str] = Field(None, description="Order status")
    payment_id: Optional[str] = Field(None, description="Payment ID")
    payment_data: Optional[Dict] = Field(None, description="Payment data")
    delivery_data: Optional[Dict] = Field(None, description="Delivery data")
    delivery_message: Optional[str] = Field(None, description="Delivery message")


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: int
    order_number: str
    user_id: int
    product_id: int
    unit_price: Decimal
    total_price: Decimal
    currency: str
    status: str
    payment_gateway: Optional[str] = None
    payment_id: Optional[str] = None
    payment_data: Optional[Dict] = None
    delivery_data: Optional[Dict] = None
    delivery_message: Optional[str] = None
    delivered_at: Optional[datetime] = None
    is_trial: bool
    referral_code: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    
    # Computed fields
    is_pending: bool
    is_completed: bool
    is_cancelled: bool
    is_expired: bool
    formatted_total: str
    
    model_config = {"from_attributes": True}


class OrderList(BaseModel):
    """Schema for order list response."""
    orders: list[OrderResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class OrderStats(BaseModel):
    """Order statistics schema."""
    total_orders: int
    pending_orders: int
    completed_orders: int
    cancelled_orders: int
    revenue_today: Decimal
    revenue_total: Decimal


class PaymentRequest(BaseModel):
    """Payment request schema."""
    order_id: int = Field(..., description="Order ID")
    payment_gateway: str = Field(..., description="Payment gateway")
    return_url: Optional[str] = Field(None, description="Return URL")


class PaymentResponse(BaseModel):
    """Payment response schema."""
    payment_id: str
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    expires_at: Optional[datetime] = None