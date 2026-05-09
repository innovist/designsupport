"""
Alembic environment - synchronous migration runner for PostgreSQL.
"""

import os
import sys
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import all models so Alembic discovers them
import app.models  # noqa: F401 - registers all ORM classes
from app.models.base import Base
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def get_url() -> str:
    return os.environ.get("DATABASE_URL", settings.database_url)


# @MX:NOTE: [AUTO] Generates SQL migration scripts without database connection - useful for CI/CD pipelines
def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    context.configure(
        url=get_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# @MX:NOTE: [AUTO] Executes migrations against live database - standard migration path for production deployments
def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    cfg = config.get_section(config.config_ini_section, {})
    cfg["sqlalchemy.url"] = get_url()

    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            include_schemas=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
