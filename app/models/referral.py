"""Referral model."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class ReferralStatus(str, Enum):
    """Referral status types."""
    PENDING = "pending"
    ACTIVE = "active"
    REWARDED = "rewarded"
    EXPIRED = "expired"


class Referral(Base):
    """Referral relationship model."""
    
    __tablename__ = "referrals"
    
    # Primary key
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    
    # Referral relationship
    referrer_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    referred_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), index=True)
    
    # Referral details
    referral_code: Mapped[str] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default=ReferralStatus.PENDING.value)
    
    # Reward tracking
    reward_given: Mapped[bool] = mapped_column(Boolean, default=False)
    reward_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    reward_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    reward_type: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # days, amount, etc.
    
    # Level tracking (for multi-level referrals)
    level: Mapped[int] = mapped_column(default=1)  # 1 = direct referral, 2 = second level
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), 
        server_default=func.now(),
        nullable=False
    )
    activated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    rewarded_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    referrer: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[referrer_id],
        back_populates="referrals"
    )
    referred: Mapped["User"] = relationship(
        "User", 
        foreign_keys=[referred_id]
    )
    
    def __repr__(self) -> str:
        return f"<Referral(id={self.id}, referrer_id={self.referrer_id}, referred_id={self.referred_id})>"
    
    @property
    def is_pending(self) -> bool:
        """Check if referral is pending."""
        return self.status == ReferralStatus.PENDING.value
    
    @property
    def is_active(self) -> bool:
        """Check if referral is active."""
        return self.status == ReferralStatus.ACTIVE.value
    
    @property
    def is_rewarded(self) -> bool:
        """Check if referral has been rewarded."""
        return self.reward_given
    
    def activate(self) -> None:
        """Activate the referral."""
        self.status = ReferralStatus.ACTIVE.value
        self.activated_at = datetime.now()
    
    def mark_as_rewarded(self, reward_amount: Optional[Decimal] = None, 
                        reward_currency: Optional[str] = None,
                        reward_type: Optional[str] = None) -> None:
        """Mark referral as rewarded."""
        self.status = ReferralStatus.REWARDED.value
        self.reward_given = True
        self.rewarded_at = datetime.now()
        
        if reward_amount:
            self.reward_amount = reward_amount
        if reward_currency:
            self.reward_currency = reward_currency
        if reward_type:
            self.reward_type = reward_type