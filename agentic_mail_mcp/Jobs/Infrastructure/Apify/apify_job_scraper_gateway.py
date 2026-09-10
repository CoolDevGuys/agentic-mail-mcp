"""Apify adapter for the JobScraperGateway port.

Uses apify-client (async, ``ApifyClientAsync``) against a private actor. The
dataset is streamed via offset/limit pagination: one page in memory at a time.

apify-client 3.x returns pydantic resource models (snake_case); older/alternate
clients may return plain dicts, so field access goes through ``_field``.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import AsyncIterator
from datetime import datetime
from typing import Any

from agentic_mail_mcp.Jobs.Domain.Gateway.job_scraper_gateway import (
    UnsupportedActorVersion,
)
from agentic_mail_mcp.Jobs.Domain.Model.scrape_run import RunStatus, ScrapeRun

logger = logging.getLogger(__name__)


def _version_tuple(value: str) -> tuple[int, ...]:
    parts = []
    for chunk in value.split(".")[:3]:
        digits = "".join(c for c in chunk if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts + [0] * (3 - len(parts)))


def _field(obj: Any, snake: str, camel: str) -> Any:
    if isinstance(obj, dict):
        return obj.get(camel)
    return getattr(obj, snake, None)


def _as_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return value
    return ScrapeRun.parse_timestamp(value)


class ApifyJobScraperGateway:
    def __init__(
        self,
        *,
        token: str,
        actor_id: str,
        minimum_actor_version: str = "0.1",
        client: Any | None = None,
    ) -> None:
        if client is None:
            from apify_client import ApifyClientAsync  # optional extra: scraping

            client = ApifyClientAsync(token=token)
        self._client = client
        self._actor_id = actor_id
        self._minimum_actor_version = minimum_actor_version

    async def ensure_compatible(self) -> str:
        # Actor versions are listed oldest first in the resource payload.
        actor = await self._client.actor(self._actor_id).get()
        versions = _field(actor, "versions", "versions") or []
        if not versions:
            raise UnsupportedActorVersion(f"actor {self._actor_id} reports no versions")
        current = str(_field(versions[-1], "version_number", "versionNumber") or "0")
        if _version_tuple(current) < _version_tuple(self._minimum_actor_version):
            raise UnsupportedActorVersion(
                f"actor {self._actor_id} is at {current}, "
                f"integration requires >= {self._minimum_actor_version}"
            )
        return current

    async def start_run(self, run_input: dict[str, Any], *, key: str) -> ScrapeRun:
        run = await self._client.actor(self._actor_id).start(run_input=run_input)
        return ScrapeRun.new(str(_field(run, "id", "id")), key=key)

    async def fetch_status(self, run_id: str) -> ScrapeRun:
        run = await self._client.run(run_id).get()
        return self._to_domain(run)

    async def await_completion(
        self, run: ScrapeRun, *, poll_secs: float = 10.0
    ) -> ScrapeRun:
        current = await self.fetch_status(run.run_id)
        while not current.status.is_terminal:
            await asyncio.sleep(poll_secs)
            current = await self.fetch_status(run.run_id)
        return current

    async def stream_items(
        self, dataset_id: str, *, page_size: int = 100
    ) -> AsyncIterator[list[dict[str, Any]]]:
        dataset = self._client.dataset(dataset_id)
        offset = 0
        while True:
            page = await dataset.list_items(offset=offset, limit=page_size)
            items = list(page.items)
            if items:
                yield items
            offset += page_size
            if offset >= page.total:
                return

    def _to_domain(self, run: Any) -> ScrapeRun:
        status = RunStatus.from_actor(str(_field(run, "status", "status") or ""))
        return ScrapeRun(
            run_id=str(_field(run, "id", "id")),
            status=status,
            dataset_id=_field(run, "default_dataset_id", "defaultDatasetId") or None,
            started_at=_as_datetime(_field(run, "started_at", "startedAt")),
            finished_at=_as_datetime(_field(run, "finished_at", "finishedAt")),
        )
