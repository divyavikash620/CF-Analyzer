from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase


# Declarative base class for SQLAlchemy 2.0 style mappings.
# Inheriting from `AsyncAttrs` makes mapped classes async-session friendly.
class Base(AsyncAttrs, DeclarativeBase):
	pass
