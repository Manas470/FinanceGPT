"""
FinanceGPT Configuration
Production-grade settings with environment variable support
"""
from pydantic_settings import BaseSettings
from typing import List, Optional
from functools import lru_cache


class Settings(BaseSettings):
    # App
    APP_NAME: str = "FinanceGPT"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # Security
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION-USE-SECRETS-MANAGER"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/financegpt"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # Anthropic / Claude AI
    ANTHROPIC_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-opus-4-6"

    # File Storage
    UPLOAD_DIR: str = "./uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = ["csv", "xlsx", "xls", "pdf"]

    # QuickBooks OAuth
    QB_CLIENT_ID: str = ""
    QB_CLIENT_SECRET: str = ""
    QB_REDIRECT_URI: str = "http://localhost:8000/api/integrations/quickbooks/callback"
    QB_ENVIRONMENT: str = "sandbox"  # sandbox | production

    # Xero OAuth
    XERO_CLIENT_ID: str = ""
    XERO_CLIENT_SECRET: str = ""
    XERO_REDIRECT_URI: str = "http://localhost:8000/api/integrations/xero/callback"

    # CORS
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://financegpt.yourdomain.com",
    ]

    # Email (optional alerts)
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # Feature Flags
    ENABLE_QUICKBOOKS: bool = True
    ENABLE_XERO: bool = True
    ENABLE_EMAIL_ALERTS: bool = False

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
