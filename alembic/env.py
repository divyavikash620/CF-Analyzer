from __future__ import with_statement

import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

# ensure project root is importable
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from app.db.base import Base
from app.core.config import get_settings

config = context.config
fileConfig(config.config_file_name)

settings = get_settings()
# Alembic expects a synchronous URL; if using an async driver we strip the +asyncpg suffix here
sqlalchemy_url = settings.DATABASE_URL
if "+asyncpg" in sqlalchemy_url:
    sqlalchemy_url = sqlalchemy_url.replace("+asyncpg", "")
config.set_main_option("sqlalchemy.url", sqlalchemy_url)

target_metadata = Base.metadata


def run_migrations_offline():
    context.configure(url=config.get_main_option("sqlalchemy.url"), target_metadata=target_metadata, literal_binds=True)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
