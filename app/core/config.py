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

    # Auth
    JWT_SECRET_KEY: str = "CHANGE_ME"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
