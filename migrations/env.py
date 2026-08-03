from __future__ import annotations

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from src.Bootstrap.Settings import Settings
from src.Common.Infrastructure.Persistence.database import Base

# Import models so their tables register on Base.metadata.
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Models import models  # noqa: F401

config = context.config

if config.config_file_name is not None:
    # disable_existing_loggers=False: fileConfig otherwise disables every logger
    # already imported (a well-known Alembic gotcha), silencing app loggers.
    fileConfig(config.config_file_name, disable_existing_loggers=False)

# The single migrations directory serves SQLite (default) and PostgreSQL.
# A caller (e.g. an integration test) may inject a url via config.attributes;
# otherwise the database url comes from Settings.
_url = config.attributes.get("sqlalchemy.url") or Settings.from_env().database.url
config.set_main_option("sqlalchemy.url", _url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
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
