from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    # Database
    DATABASE_URL: str = "sqlite:///./newsradar.db"

    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Email
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM: str = "noreply@newsradar.com"

    # Application
    APP_NAME: str = "NewsRadar"
    APP_VERSION: str = "1.0.0"

    # RSS Processing
    RSS_FETCH_TIMEOUT: int = 30
    MAX_ALERTS_PER_USER: int = 20
    MIN_SYNONYMS: int = 3
    MAX_SYNONYMS: int = 10

    class Config:
        """Pydantic config."""

        env_file = ".env"


settings = Settings()
