from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    PROJECT_NAME: str = "cp-analyser"
    DEBUG: bool = True

    # Database (asyncpg) - required
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Redis / Celery (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Auth - SECRET_KEY has a default fallback for testing
    SECRET_KEY: str = "test-secret-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Get cached Settings instance.
    
    Uses @lru_cache to ensure only one Settings instance is created per application lifetime.
    The .env file is automatically loaded on the first call.
    Settings are then cached for the duration of the application.
    """
    return Settings()
