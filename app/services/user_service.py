"""User service for managing users and authentication."""
import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.user import User
from app.models.referral import Referral, ReferralStatus
from app.schemas.user import UserCreate, UserUpdate, UserResponse, UserStats
from app.config import settings

logger = logging.getLogger(__name__)


class UserService:
    """Service for user management."""
    
    @staticmethod
    async def get_by_telegram_id(telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        async with get_session() as session:
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_id(user_id: int) -> Optional[User]:
        """Get user by ID."""
        async with get_session() as session:
            query = select(User).where(User.id == user_id)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def get_by_referral_code(referral_code: str) -> Optional[User]:
        """Get user by referral code."""
        async with get_session() as session:
            query = select(User).where(User.referral_code == referral_code)
            result = await session.execute(query)
            return result.scalar_one_or_none()
    
    @staticmethod
    async def create_user(user_data: UserCreate, referrer_code: Optional[str] = None) -> User:
        """Create a new user."""
        async with get_session() as session:
            # Check if user already exists
            existing_user = await UserService.get_by_telegram_id(user_data.telegram_id)
            if existing_user:
                return existing_user
            
            # Generate unique referral code
            referral_code = UserService._generate_referral_code()
            while await UserService.get_by_referral_code(referral_code):
                referral_code = UserService._generate_referral_code()
            
            # Find referrer if code provided
            referrer_id = None
            if referrer_code:
                referrer = await UserService.get_by_referral_code(referrer_code)
                if referrer:
                    referrer_id = referrer.id
            
            # Create user
            user = User(
                telegram_id=user_data.telegram_id,
                username=user_data.username,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                language_code=user_data.language_code or "en",
                referral_code=referral_code,
                referrer_id=referrer_id,
                last_activity=datetime.now()
            )
            
            session.add(user)
            await session.flush()  # Get user ID
            
            # Create referral relationship if there's a referrer
            if referrer_id and referrer_code:
                referral = Referral(
                    referrer_id=referrer_id,
                    referred_id=user.id,
                    referral_code=referrer_code,
                    status=ReferralStatus.ACTIVE.value
                )
                session.add(referral)
                
                # Update referrer's total_referred count
                referrer = await session.get(User, referrer_id)
                if referrer:
                    referrer.total_referred += 1
            
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Created new user: {user.telegram_id} (ID: {user.id})")
            return user
    
    @staticmethod
    async def update_user(user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user information."""
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return None
            
            update_data = user_data.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(user, field, value)
            
            user.updated_at = datetime.now()
            await session.commit()
            await session.refresh(user)
            
            logger.info(f"Updated user: {user.telegram_id}")
            return user
    
    @staticmethod
    async def update_activity(telegram_id: int) -> None:
        """Update user's last activity."""
        async with get_session() as session:
            query = select(User).where(User.telegram_id == telegram_id)
            result = await session.execute(query)
            user = result.scalar_one_or_none()
            
            if user:
                user.last_activity = datetime.now()
                await session.commit()
    
    @staticmethod
    async def activate_trial(user_id: int) -> bool:
        """Activate trial for user."""
        if not settings.trial_enabled:
            return False
        
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user or user.trial_used:
                return False
            
            now = datetime.now()
            user.trial_used = True
            user.trial_start = now
            user.trial_end = now + timedelta(days=settings.trial_duration_days)
            
            await session.commit()
            logger.info(f"Activated trial for user: {user.telegram_id}")
            return True
    
    @staticmethod
    async def ban_user(user_id: int, ban: bool = True) -> bool:
        """Ban or unban user."""
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            
            user.is_banned = ban
            user.updated_at = datetime.now()
            await session.commit()
            
            action = "banned" if ban else "unbanned"
            logger.info(f"User {user.telegram_id} {action}")
            return True
    
    @staticmethod
    async def make_admin(user_id: int, admin: bool = True) -> bool:
        """Make user admin or remove admin rights."""
        async with get_session() as session:
            user = await session.get(User, user_id)
            if not user:
                return False
            
            user.is_admin = admin
            user.updated_at = datetime.now()
            await session.commit()
            
            action = "granted admin" if admin else "removed admin"
            logger.info(f"User {user.telegram_id} {action} rights")
            return True
    
    @staticmethod
    async def get_user_stats() -> UserStats:
        """Get user statistics."""
        async with get_session() as session:
            # Total users
            total_query = select(func.count(User.id))
            total_result = await session.execute(total_query)
            total_users = total_result.scalar() or 0
            
            # Active users
            active_query = select(func.count(User.id)).where(User.is_active == True)
            active_result = await session.execute(active_query)
            active_users = active_result.scalar() or 0
            
            # Trial users
            trial_query = select(func.count(User.id)).where(User.trial_used == True)
            trial_result = await session.execute(trial_query)
            trial_users = trial_result.scalar() or 0
            
            # Admin users
            admin_query = select(func.count(User.id)).where(User.is_admin == True)
            admin_result = await session.execute(admin_query)
            admin_users = admin_result.scalar() or 0
            
            # New users today
            today = datetime.now().date()
            new_today_query = select(func.count(User.id)).where(
                func.date(User.created_at) == today
            )
            new_today_result = await session.execute(new_today_query)
            new_users_today = new_today_result.scalar() or 0
            
            return UserStats(
                total_users=total_users,
                active_users=active_users,
                trial_users=trial_users,
                admin_users=admin_users,
                new_users_today=new_users_today
            )
    
    @staticmethod
    def _generate_referral_code(length: int = 8) -> str:
        """Generate a random referral code."""
        chars = string.ascii_letters + string.digits
        return ''.join(secrets.choice(chars) for _ in range(length))