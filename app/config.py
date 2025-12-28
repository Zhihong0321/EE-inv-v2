from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # JWT
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 43200  # 30 days

    # WhatsApp API
    WHATSAPP_API_URL: str = "https://whatsapp-api-server-production-c15f.up.railway.app/api"
    WHATSAPP_CHECK_INTERVAL: int = 5  # seconds between status checks

    # OTP Settings
    OTP_EXPIRE_SECONDS: int = 1800  # 30 minutes
    OTP_LENGTH: int = 6

    # Invoice Settings
    INVOICE_NUMBER_PREFIX: str = "INV"
    INVOICE_NUMBER_LENGTH: int = 6
    DEFAULT_SST_RATE: float = 8.0
    SHARE_LINK_EXPIRY_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
