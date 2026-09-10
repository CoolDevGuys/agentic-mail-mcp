"""JobsSink that publishes scraped pages onto the shared event bus."""

from __future__ import annotations

import logging
from typing import Any

from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Jobs.Domain.Events.jobs_scraped import JobsScraped

logger = logging.getLogger(__name__)


class EventPublishingJobSink:
    """Default sink: publishes one JobsScraped event per ingested page.

    Subscribers (e.g. a future jobs persistence handler) fan out from the bus;
    the sink itself stays storage-free.
    """

    def __init__(self, event_bus: EventBus, *, run_id: str = "unknown") -> None:
        self._event_bus = event_bus
        self._run_id = run_id

    def bind(self, run_id: str) -> None:
        self._run_id = run_id

    async def ingest_page(self, items: list[dict[str, Any]]) -> None:
        self._event_bus.publish(
            JobsScraped(
                event_type="jobs.scraped", run_id=self._run_id, count=len(items)
            )
        )
