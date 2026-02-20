from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "cp-analyser"
    DEBUG: bool = True

    # Database (asyncpg) - required
    DATABASE_URL: str
    SQLALCHEMY_ECHO: bool = False

    # Redis / Celery (optional)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Auth
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Single global settings instance. Import `settings` from other modules for reuse.
settings = Settings()


def get_settings() -> Settings:
    """Return the global Settings instance. Kept for backward compatibility."""
    return settings
