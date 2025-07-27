"""User schemas."""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class UserBase(BaseModel):
    """Base user schema."""
    telegram_id: int = Field(..., description="Telegram user ID")
    username: Optional[str] = Field(None, description="Telegram username")
    first_name: Optional[str] = Field(None, description="First name")
    last_name: Optional[str] = Field(None, description="Last name")
    language_code: Optional[str] = Field("en", description="Language code")


class UserCreate(UserBase):
    """Schema for creating a user."""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    language_code: Optional[str] = None
    is_active: Optional[bool] = None
    is_banned: Optional[bool] = None


class UserResponse(UserBase):
    """Schema for user response."""
    id: int
    is_active: bool
    is_banned: bool
    is_admin: bool
    trial_used: bool
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    referrer_id: Optional[int] = None
    referral_code: Optional[str] = None
    total_referred: int
    created_at: datetime
    updated_at: datetime
    last_activity: Optional[datetime] = None
    
    model_config = {"from_attributes": True}


class UserStats(BaseModel):
    """User statistics schema."""
    total_users: int
    active_users: int
    trial_users: int
    admin_users: int
    new_users_today: int