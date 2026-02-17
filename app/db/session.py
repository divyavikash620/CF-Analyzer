from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import get_settings

settings = get_settings()

# Async SQLAlchemy engine + sessionmaker (SQLAlchemy 2.0 async API)
engine = create_async_engine(settings.DATABASE_URL, echo=settings.SQLALCHEMY_ECHO, future=True)
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session.

    Usage:
        async def endpoint(db: AsyncSession = Depends(get_async_session)):
            ...
    """
    async with AsyncSessionLocal() as session:
        yield session
