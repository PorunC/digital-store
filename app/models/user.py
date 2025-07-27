"""User model."""
from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    """User model for Telegram users."""
    
    __tablename__ = "users"
    
    # Primary key
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    
    # Telegram info
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), default="en")
    
    # User status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    
    # Trial system
    trial_used: Mapped[bool] = mapped_column(Boolean, default=False)
    trial_start: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    trial_end: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Referral system
    referrer_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    referral_code: Mapped[Optional[str]] = mapped_column(String(50), unique=True, nullable=True, index=True)
    total_referred: Mapped[int] = mapped_column(default=0)
    
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
    last_activity: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), 
        nullable=True
    )
    
    # Relationships
    orders: Mapped[list["Order"]] = relationship("Order", back_populates="user")
    referrals: Mapped[list["Referral"]] = relationship(
        "Referral", 
        foreign_keys="Referral.referrer_id",
        back_populates="referrer"
    )
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, telegram_id={self.telegram_id}, username={self.username})>"
    
    @property
    def display_name(self) -> str:
        """Get user display name."""
        if self.username:
            return f"@{self.username}"
        elif self.first_name:
            name = self.first_name
            if self.last_name:
                name += f" {self.last_name}"
            return name
        else:
            return f"User#{self.telegram_id}"
    
    @property
    def has_active_trial(self) -> bool:
        """Check if user has active trial."""
        if not self.trial_start or not self.trial_end:
            return False
        now = datetime.now()
        return self.trial_start <= now <= self.trial_end
    
    def is_referrer_of(self, user_id: int) -> bool:
        """Check if this user is referrer of another user."""
        return any(ref.referred_id == user_id for ref in self.referrals)