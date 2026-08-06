"""Programmatic Alembic upgrade for application startup.

Keeps the Alembic migration as the single source of truth for the schema so
runtime does not diverge from ``migrations/``.
"""

from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config

# migrations_runner.py -> Persistence -> Infrastructure -> Common -> agentic_mail_mcp -> repo root
_REPO_ROOT = Path(__file__).resolve().parents[4]


def apply_migrations(database_url: str) -> None:
    """Run ``alembic upgrade head`` against ``database_url``."""
    config = Config(str(_REPO_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(_REPO_ROOT / "migrations"))
    # env.py reads this injected url instead of Settings.
    config.attributes["sqlalchemy.url"] = database_url
    command.upgrade(config, "head")
