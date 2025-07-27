"""Product schemas."""
from datetime import datetime
from decimal import Decimal
from typing import Dict, Optional

from pydantic import BaseModel, Field

from app.models.product import DeliveryType, ProductCategory


class ProductBase(BaseModel):
    """Base product schema."""
    name: str = Field(..., min_length=1, max_length=255, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category: str = Field(default=ProductCategory.DIGITAL.value, description="Product category")
    price: Decimal = Field(..., gt=0, description="Product price")
    currency: str = Field(default="RUB", description="Price currency")
    delivery_type: str = Field(default=DeliveryType.INSTANT.value, description="Delivery type")
    duration_days: Optional[int] = Field(None, ge=0, description="Duration in days (0 for permanent)")


class ProductCreate(ProductBase):
    """Schema for creating a product."""
    stock_count: Optional[int] = Field(None, ge=0, description="Stock count (None for unlimited)")
    delivery_config: Optional[Dict] = Field(None, description="Delivery configuration")
    is_active: bool = Field(default=True, description="Is product active")
    is_featured: bool = Field(default=False, description="Is product featured")
    slug: Optional[str] = Field(None, description="Product slug")
    image_url: Optional[str] = Field(None, description="Product image URL")
    sort_order: int = Field(default=0, description="Sort order")


class ProductUpdate(BaseModel):
    """Schema for updating a product."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = Field(None, gt=0)
    currency: Optional[str] = None
    delivery_type: Optional[str] = None
    duration_days: Optional[int] = Field(None, ge=0)
    stock_count: Optional[int] = Field(None, ge=0)
    delivery_config: Optional[Dict] = None
    is_active: Optional[bool] = None
    is_featured: Optional[bool] = None
    slug: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: Optional[int] = None


class ProductResponse(ProductBase):
    """Schema for product response."""
    id: int
    stock_count: Optional[int] = None
    sold_count: int
    delivery_config: Optional[Dict] = None
    is_active: bool
    is_featured: bool
    slug: Optional[str] = None
    image_url: Optional[str] = None
    sort_order: int
    created_at: datetime
    updated_at: datetime
    
    # Computed fields
    is_in_stock: bool
    is_available: bool
    formatted_price: str
    
    model_config = {"from_attributes": True}


class ProductList(BaseModel):
    """Schema for product list response."""
    products: list[ProductResponse]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ProductStats(BaseModel):
    """Product statistics schema."""
    total_products: int
    active_products: int
    out_of_stock: int
    total_sales: int
    revenue_today: Decimal