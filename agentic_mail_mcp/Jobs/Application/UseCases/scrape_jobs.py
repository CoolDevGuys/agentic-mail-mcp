"""Use case: trigger a scrape run and stream its results into the jobs pipeline.

Re-attach contract: the run record is persisted right after starting, before
any long wait. If this process dies mid-run, the next execute() with the same
key finds the record, refreshes its status against the actor, and joins the
existing run instead of starting a duplicate (a duplicate doubles proxy spend).
Completed/failed records are replaced by a fresh run; a run still in progress
is never duplicated.
"""

from __future__ import annotations

import logging
from typing import Any

from agentic_mail_mcp.Jobs.Domain.Gateway.job_scraper_gateway import JobScraperGateway
from agentic_mail_mcp.Jobs.Domain.Gateway.jobs_sink import JobsSink
from agentic_mail_mcp.Jobs.Domain.Model.scrape_run import RunStatus, ScrapeRun
from agentic_mail_mcp.Jobs.Domain.Repository.scrape_run_repository import (
    ScrapeRunRepository,
)

logger = logging.getLogger(__name__)


class ScrapeAlreadyInProgress(Exception):
    """Another process holds a fresh claim to start a run for this key."""


class ScrapeJobsUseCase:
    def __init__(
        self,
        gateway: JobScraperGateway,
        runs: ScrapeRunRepository,
        *,
        page_size: int = 100,
    ) -> None:
        self._gateway = gateway
        self._runs = runs
        self._page_size = page_size

    async def execute(
        self,
        run_input: dict[str, Any],
        sink: JobsSink,
        *,
        key: str = "default",
    ) -> ScrapeRun:
        await self._gateway.ensure_compatible()

        run = await self._start_or_attach(key, run_input)
        bind = getattr(sink, "bind", None)
        if bind is not None:
            # Optional structural hook: sinks that need the run id (e.g. the
            # event-publishing default) learn it here.
            bind(run.run_id)
        if run.status.is_terminal and run.status is not RunStatus.SUCCEEDED:
            logger.warning(
                "Attached run did not succeed; not ingesting",
                extra={"run_id": run.run_id, "status": run.status.value},
            )
            return run

        run = (
            await self._gateway.await_completion(run)
            if run.status is not RunStatus.SUCCEEDED
            else run
        )
        if run.status is not RunStatus.SUCCEEDED or not run.dataset_id:
            return run

        ingested = run.items_ingested
        async for page in self._gateway.stream_items(
            run.dataset_id, page_size=self._page_size
        ):
            await sink.ingest_page(page)
            ingested += len(page)
            run = ScrapeRun(
                run_id=run.run_id,
                status=run.status,
                dataset_id=run.dataset_id,
                key=run.key,
                started_at=run.started_at,
                finished_at=run.finished_at,
                items_ingested=ingested,
            )
            self._runs.save(run)
        return run

    async def _start_or_attach(self, key: str, run_input: dict[str, Any]) -> ScrapeRun:
        existing = self._runs.load(key)
        if existing is not None:
            current = await self._gateway.fetch_status(existing.run_id)
            if not current.status.is_terminal:
                logger.info(
                    "Re-attaching to in-progress run", extra={"run_id": current.run_id}
                )
                self._runs.save(current)
                return current
            if current.status is RunStatus.SUCCEEDED and current.items_ingested == 0:
                # Finished while we were down, results never ingested: ingest now.
                logger.info(
                    "Resuming ingest of finished run", extra={"run_id": current.run_id}
                )
                return current
            self._runs.clear(key)

        if not self._runs.claim(key):
            raise ScrapeAlreadyInProgress(
                f"a scrape run is already being started for key {key!r}"
            )
        run = await self._gateway.start_run(run_input, key=key)
        # Persisted immediately; the minutes-long wait below is crash-safe.
        self._runs.save(run)
        logger.info("Started scrape run", extra={"run_id": run.run_id})
        return run
