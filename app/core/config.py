from functools import lru_cache
from pydantic import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "cp-analyser"
    DEBUG: bool = True

    # Database (asyncpg)
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/cpanalyser"
    SQLALCHEMY_ECHO: bool = False

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # Auth (set `SECRET_KEY` via environment variable or in `.env` for local dev)
    # Example: export SECRET_KEY="<your-secret>"
    SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    # Access token expiry in minutes (recommended 15-30)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
