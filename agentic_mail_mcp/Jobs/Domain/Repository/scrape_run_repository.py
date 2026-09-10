"""Port for persisting scrape run lifecycle records (re-attach, not double-trigger)."""

from __future__ import annotations

from typing import Protocol

from ..Model.scrape_run import ScrapeRun


class ScrapeRunRepository(Protocol):
    def load(self, key: str) -> ScrapeRun | None: ...

    def save(self, run: ScrapeRun) -> None: ...

    def clear(self, key: str) -> None: ...
