"""Port for the external actor that scrapes job listings."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Any, Protocol

from ..Model.scrape_run import ScrapeRun


class UnsupportedActorVersion(Exception):
    """The deployed actor is older than the version this integration needs."""


class JobScraperGateway(Protocol):
    """Runs the job-scraper actor and exposes its dataset.

    Implementations are async; run lifecycle is tracked by the caller via
    :class:`ScrapeRunRepository`, so these methods are thin and stateless.
    """

    async def ensure_compatible(self) -> str:
        """Verify the deployed actor meets the pinned minimum version.

        Returns the observed version; raises UnsupportedActorVersion otherwise.
        """
        ...

    async def start_run(self, run_input: dict[str, Any], *, key: str) -> ScrapeRun:
        """Trigger a run with the given input and return immediately."""
        ...

    async def fetch_status(self, run_id: str) -> ScrapeRun:
        """Current state of an existing run (re-attach path)."""
        ...

    async def await_completion(
        self, run: ScrapeRun, *, poll_secs: float = 10.0
    ) -> ScrapeRun:
        """Poll until the run reaches a terminal state."""
        ...

    def stream_items(
        self, dataset_id: str, *, page_size: int = 100
    ) -> AsyncIterator[list[dict[str, Any]]]:
        """Yield dataset items page by page; never buffer the full dataset."""
        ...
