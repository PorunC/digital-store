"""Application configuration management."""
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"


class Currency(str, Enum):
    """Supported currencies."""
    RUB = "RUB"
    USD = "USD"
    EUR = "EUR"
    XTR = "XTR"  # Telegram Stars


class Settings(BaseSettings):
    """Application settings."""
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    
    # Telegram Bot
    bot_token: str = Field(..., description="Telegram bot token")
    bot_domain: Optional[str] = Field(default=None, description="Bot webhook domain")
    bot_webhook_path: str = Field(default="/webhook", description="Webhook path")
    
    # Admin
    admin_ids: list[int] = Field(default_factory=list, description="Admin user IDs")
    developer_id: Optional[int] = Field(default=None, description="Developer ID")
    
    # Database
    database_url: str = Field(
        default="sqlite+aiosqlite:///./data/store.db",
        description="Database connection URL"
    )
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    
    # Payment Gateways
    telegram_stars_enabled: bool = Field(default=True, description="Enable Telegram Stars")
    cryptomus_enabled: bool = Field(default=False, description="Enable Cryptomus")
    cryptomus_api_key: Optional[str] = Field(default=None, description="Cryptomus API key")
    cryptomus_merchant_id: Optional[str] = Field(default=None, description="Cryptomus merchant ID")
    
    # Business Logic
    default_currency: Currency = Field(default=Currency.RUB, description="Default currency")
    trial_enabled: bool = Field(default=True, description="Enable trial system")
    trial_duration_days: int = Field(default=3, description="Trial duration in days")
    referral_enabled: bool = Field(default=True, description="Enable referral system")
    referral_reward_days: int = Field(default=7, description="Referral reward in days")
    
    # File Paths
    data_dir: Path = Field(default=Path("data"), description="Data directory")
    products_file: Path = Field(default=Path("data/products.json"), description="Products file")
    locales_dir: Path = Field(default=Path("locales"), description="Locales directory")
    
    # Logging
    log_level: str = Field(default="INFO", description="Log level")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format"
    )

    @property
    def webhook_url(self) -> Optional[str]:
        """Get full webhook URL."""
        if self.bot_domain:
            return f"https://{self.bot_domain}{self.bot_webhook_path}"
        return None

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == Environment.PRODUCTION


# Global settings instance
settings = Settings()