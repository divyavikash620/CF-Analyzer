"""Central DB helpers for Alembic and app-wide imports.

This module exposes the `Base` declarative class and `metadata` for Alembic
to import without pulling in the async engine or session machinery.
"""
from .base import Base

# Export metadata for Alembic
metadata = Base.metadata

__all__ = ["Base", "metadata"]
