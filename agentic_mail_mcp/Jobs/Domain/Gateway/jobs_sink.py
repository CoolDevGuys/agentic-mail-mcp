"""Port for ingesting scraped jobs into the jobs pipeline."""

from __future__ import annotations

from typing import Any, Protocol


class JobsSink(Protocol):
    """Consumes scraped job items in bounded pages.

    Implementations must not assume more than one page is in memory at a time.
    Raising aborts the ingest run with the error surfaced to the caller.
    """

    async def ingest_page(self, items: list[dict[str, Any]]) -> None: ...
