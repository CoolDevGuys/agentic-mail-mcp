import contextlib
from typing import Any

from src.Bootstrap.Settings import Settings


@contextlib.asynccontextmanager
async def lifespan(app: Any) -> Any:
    settings = Settings.from_env()

    # Startup
    await _startup(settings)

    yield {"settings": settings}

    # Shutdown
    await _shutdown(settings)


async def _startup(settings: Settings) -> None:
    # Initialize DB connection pool
    # Warm OAuth token
    # Register domain event handlers
    pass


async def _shutdown(settings: Settings) -> None:
    # Close DB connections
    # Flush audit log
    # Unsubscribe from Gmail push notifications
    pass
