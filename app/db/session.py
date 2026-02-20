from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.engine import URL

from app.core.config import get_settings

settings = get_settings()


# Create a single engine instance (module-level) so it's created only once.
# Use SQLAlchemy 2.0 async engine with `asyncpg` driver (DATABASE_URL should start with
# postgresql+asyncpg://...). The `future=True` flag aligns with SQLAlchemy 2.0 style.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.SQLALCHEMY_ECHO,
    future=True,
)


# Async session factory. `expire_on_commit=False` is important for async patterns
# where returning ORM objects after commit is expected without lazy-refresh.
AsyncSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async DB session.

    Usage:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    The session is closed automatically when the request finishes.
    """
    async with AsyncSessionLocal() as session:
        yield session


# Backwards-compatible alias used elsewhere in the codebase
get_async_session = get_db
