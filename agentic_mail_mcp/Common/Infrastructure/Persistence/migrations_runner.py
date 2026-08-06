"""Programmatic Alembic upgrade for application startup.

Keeps the Alembic migration as the single source of truth for the schema so
runtime does not diverge from ``migrations/``.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

# The Alembic scripts ship *inside* the package so they resolve identically from
# a source checkout and a pip-installed wheel. Path:
# migrations_runner.py -> Persistence -> Infrastructure -> Common -> agentic_mail_mcp
_MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "migrations"


def apply_migrations(database_url: str) -> None:
    """Run ``alembic upgrade head`` against ``database_url``."""
    # Build the config programmatically (no on-disk alembic.ini needed at
    # runtime): the app configures its own logging, and env.py reads the url
    # from ``config.attributes``.
    config = Config()
    config.set_main_option("script_location", str(_MIGRATIONS_DIR))
    config.attributes["sqlalchemy.url"] = database_url
    command.upgrade(config, "head")
