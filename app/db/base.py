from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import declarative_base

# All ORM models should inherit from this `Base`.
# Use `AsyncAttrs` so the mapped attributes are async-compatible
# when using SQLAlchemy's async ORM (AsyncSession).
Base = declarative_base(cls=AsyncAttrs)
