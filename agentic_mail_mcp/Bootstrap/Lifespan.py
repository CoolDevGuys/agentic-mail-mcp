import contextlib
import logging
import os
from pathlib import Path
from typing import Any
from urllib.parse import unquote

from agentic_mail_mcp.Bootstrap.Settings import Settings

logger = logging.getLogger(__name__)


@contextlib.asynccontextmanager
async def lifespan(app: Any) -> Any:
    settings = Settings.from_env()

    # Startup
    await _startup(settings)

    yield {"settings": settings}

    # Shutdown
    await _shutdown(settings)


async def _startup(settings: Settings) -> None:
    _validate_db_path(settings.database.url)
    logger.info("Startup complete")


async def _shutdown(settings: Settings) -> None:
    logger.info("Shutdown complete")


def _validate_db_path(url: str) -> None:
    if not url.startswith("sqlite"):
        return
    if url in ("sqlite://", "sqlite:///:memory:"):
        return
    # Extract path: strip "sqlite:///" (3 slashes) or "sqlite://" (2 slashes) prefix.
    # sqlite:///./db.db -> ./db.db
    # sqlite:////var/lib/db.db -> /var/lib/db.db
    if url.startswith("sqlite:///"):
        file_path = url[len("sqlite:///"):]
    elif url.startswith("sqlite://"):
        file_path = url[len("sqlite://"):]
    else:
        file_path = url.split("sqlite", 1)[1]
    file_path = unquote(file_path)
    db_path = Path(file_path).expanduser()
    parent = db_path.parent
    if parent and parent != Path("/") and not parent.exists():
        try:
            parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.error(
                "Cannot create database directory '%s': %s. "
                "Set AGENTIC_MAIL_MCP_DATABASE_URL to a writable path.",
                parent,
                exc,
            )
            raise SystemExit(1) from exc
    if parent and not os.access(parent, os.W_OK):
        logger.error(
            "Database directory '%s' is not writable. "
            "Set AGENTIC_MAIL_MCP_DATABASE_URL to a writable path.",
            parent,
        )
        raise SystemExit(1)
    if db_path.exists() and not os.access(str(db_path), os.W_OK):
        logger.error(
            "Database file '%s' is not writable. "
            "Check file permissions or set AGENTIC_MAIL_MCP_DATABASE_URL to a writable path.",
            db_path,
        )
        raise SystemExit(1)
