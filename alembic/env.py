import os
import sys
import importlib
import pkgutil

from alembic import context
from sqlalchemy import engine_from_config, pool

# Ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.core.config import get_settings
import app.models as app_models

# Import all models so Base.metadata includes them
for _, name, _ in pkgutil.iter_modules(app_models.__path__):
    importlib.import_module(f"{app_models.__name__}.{name}")

config = context.config

settings = get_settings()

# Strip +asyncpg for Alembic (sync engine)
sqlalchemy_url = settings.DATABASE_URL
if "+asyncpg" in sqlalchemy_url:
    sqlalchemy_url = sqlalchemy_url.replace("+asyncpg", "")

config.set_main_option("sqlalchemy.url", sqlalchemy_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
