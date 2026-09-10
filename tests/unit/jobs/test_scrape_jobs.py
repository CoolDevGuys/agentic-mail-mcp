"""Offline tests for the job-scraping integration (fakes, no network)."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest

from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.Jobs.Application.UseCases.scrape_jobs import ScrapeJobsUseCase
from agentic_mail_mcp.Jobs.Domain.Gateway.job_scraper_gateway import (
    UnsupportedActorVersion,
)
from agentic_mail_mcp.Jobs.Domain.Model.scrape_run import RunStatus, ScrapeRun
from agentic_mail_mcp.Jobs.Infrastructure.Apify.apify_job_scraper_gateway import (
    ApifyJobScraperGateway,
    _version_tuple,
)
from agentic_mail_mcp.Jobs.Infrastructure.Storage.json_scrape_run_repository import (
    JsonScrapeRunRepository,
)


class InMemoryRunRepository:
    def __init__(self) -> None:
        self.data: dict[str, ScrapeRun] = {}

    def load(self, key: str) -> ScrapeRun | None:
        return self.data.get(key)

    def save(self, run: ScrapeRun) -> None:
        self.data[run.key] = run

    def clear(self, key: str) -> None:
        self.data.pop(key, None)


class FakeGateway:
    def __init__(
        self,
        *,
        pages: list[list[dict[str, Any]]] | None = None,
        version: str = "0.1.9",
    ) -> None:
        self.pages = pages or [[{"jobId": "1"}], [{"jobId": "2"}, {"jobId": "3"}]]
        self.started: list[dict[str, Any]] = []
        self.ingested_dataset: str | None = None
        self.version = version

    async def ensure_compatible(self) -> str:
        if self.version == "too_low":
            raise UnsupportedActorVersion("0.1.0 < 0.1.9")
        return self.version

    async def start_run(self, run_input: dict[str, Any], *, key: str) -> ScrapeRun:
        self.started.append(run_input)
        return ScrapeRun.new(f"run-{len(self.started)}", key=key)

    async def fetch_status(self, run_id: str) -> ScrapeRun:
        return ScrapeRun(run_id=run_id, status=RunStatus.RUNNING)

    async def await_completion(
        self, run: ScrapeRun, *, poll_secs: float = 10.0
    ) -> ScrapeRun:
        return ScrapeRun(
            run_id=run.run_id,
            status=RunStatus.SUCCEEDED,
            dataset_id=f"ds-{run.run_id}",
            key=run.key,
            started_at=run.started_at,
        )

    async def stream_items(self, dataset_id: str, *, page_size: int = 100):
        self.ingested_dataset = dataset_id
        for page in self.pages:
            yield page


class RecordingSink:
    def __init__(self) -> None:
        self.pages: list[list[dict[str, Any]]] = []

    async def ingest_page(self, items: list[dict[str, Any]]) -> None:
        self.pages.append(items)


def run(coro):
    return asyncio.run(coro)


class TestScrapeJobsUseCase:
    def test_trigger_await_stream(self):
        gateway, repo, sink = FakeGateway(), InMemoryRunRepository(), RecordingSink()
        use_case = ScrapeJobsUseCase(gateway, repo)

        result = run(use_case.execute({"searches": [{"keywords": "x"}]}, sink))

        assert result.status is RunStatus.SUCCEEDED
        assert result.items_ingested == 3
        assert [len(p) for p in sink.pages] == [1, 2]
        assert len(gateway.started) == 1
        assert repo.data["default"].items_ingested == 3

    def test_run_persisted_before_completion(self):
        # A gateway that never finishes still leaves a RUNNING record for re-attach.
        class HangingGateway(FakeGateway):
            async def await_completion(self, run_obj, *, poll_secs: float = 10.0):
                raise asyncio.CancelledError

        repo = InMemoryRunRepository()
        with pytest.raises(asyncio.CancelledError):
            run(
                ScrapeJobsUseCase(HangingGateway(), repo).execute(
                    {"a": 1}, RecordingSink()
                )
            )
        saved = repo.data["default"]
        assert saved.status is RunStatus.RUNNING

    def test_crash_reattach_does_not_double_trigger(self):
        repo = InMemoryRunRepository()
        repo.save(ScrapeRun.new("run-existing", key="default"))

        gateway = FakeGateway()
        result = run(
            ScrapeJobsUseCase(gateway, repo).execute({"a": 1}, RecordingSink())
        )

        assert gateway.started == []  # no duplicate trigger
        assert result.run_id == "run-existing"

    def test_finished_uningested_run_is_resumed_not_restarted(self):
        repo = InMemoryRunRepository()
        repo.save(
            ScrapeRun(
                run_id="run-done",
                status=RunStatus.SUCCEEDED,
                dataset_id="ds-1",
                key="default",
            )
        )

        class DoneGateway(FakeGateway):
            async def fetch_status(self, run_id):
                return ScrapeRun(
                    run_id=run_id,
                    status=RunStatus.SUCCEEDED,
                    dataset_id="ds-1",
                    key="default",
                )

        gateway = DoneGateway()
        sink = RecordingSink()
        result = run(ScrapeJobsUseCase(gateway, repo).execute({"a": 1}, sink))
        assert gateway.started == []
        assert result.items_ingested == 3

    def test_failed_run_starts_fresh_run(self):
        repo = InMemoryRunRepository()
        repo.save(ScrapeRun(run_id="run-old", status=RunStatus.FAILED, key="default"))

        class FailedGateway(FakeGateway):
            async def fetch_status(self, run_id):
                return ScrapeRun(run_id=run_id, status=RunStatus.FAILED)

        gateway = FailedGateway()
        result = run(
            ScrapeJobsUseCase(gateway, repo).execute({"a": 1}, RecordingSink())
        )
        assert len(gateway.started) == 1
        assert result.run_id != "run-old"

    def test_min_version_enforced_before_trigger(self):
        gateway = FakeGateway(version="too_low")
        repo = InMemoryRunRepository()
        with pytest.raises(UnsupportedActorVersion):
            run(ScrapeJobsUseCase(gateway, repo).execute({"a": 1}, RecordingSink()))
        assert gateway.started == []
        assert repo.data == {}


class TestJsonRepository:
    def test_roundtrip_and_clear(self, tmp_path):
        repo = JsonScrapeRunRepository(tmp_path)
        assert repo.load("missing") is None
        run_obj = ScrapeRun.new("run-1", key="k")
        repo.save(run_obj)
        loaded = repo.load("k")
        assert loaded == run_obj
        repo.clear("k")
        assert repo.load("k") is None
        repo.clear("k")  # idempotent

    def test_corrupt_record_reads_as_absent(self, tmp_path):
        repo = JsonScrapeRunRepository(tmp_path)
        repo.save(ScrapeRun.new("run-1", key="k"))
        path = repo._path("k")
        path.write_text("{not json", encoding="utf-8")
        assert repo.load("k") is None


class TestVersionTuple:
    @pytest.mark.parametrize(
        ("a", "b", "expected"),
        [
            ("0.1.9", "0.1.8", True),
            ("0.1.9", "0.1.9", False),
            ("0.2.0", "0.10.0", False),
            ("1", "0.9.9", True),
        ],
    )
    def test_compare(self, a, b, expected):
        assert (_version_tuple(a) > _version_tuple(b)) is expected

    def test_numeric_not_lexicographic(self):
        assert _version_tuple("0.2.0") < _version_tuple("0.10.0")
        assert _version_tuple("0.1.9") >= _version_tuple("0.1.9")


class TestApifyGatewayPagination:
    def test_streams_pages_until_total(self):
        class FakePage:
            def __init__(self, items, total):
                self.items = items
                self.total = total

        class FakeDataset:
            def __init__(self):
                self.calls: list[tuple[int, int]] = []

            async def list_items(self, *, offset, limit):
                self.calls.append((offset, limit))
                if offset == 0:
                    return FakePage([{"i": 1}, {"i": 2}], 3)
                if offset == 2:
                    return FakePage([{"i": 3}], 3)
                raise AssertionError("paged past total")

        dataset = FakeDataset()

        class FakeClient:
            def dataset(self, dataset_id):
                assert dataset_id == "ds-1"
                return dataset

        async def collect():
            gateway = ApifyJobScraperGateway(
                token="t", actor_id="a", client=FakeClient()
            )
            return [page async for page in gateway.stream_items("ds-1", page_size=2)]

        pages = run(collect())
        assert pages == [[{"i": 1}, {"i": 2}], [{"i": 3}]]
        assert dataset.calls == [(0, 2), (2, 2)]


class TestFeatureFlag:
    def test_integration_off_by_default(self):
        from agentic_mail_mcp.Bootstrap.Composition import build_scrape_jobs

        # No env file: flag defaults to off regardless of token presence.
        settings = Settings()
        assert settings.apify_jobs.enabled is False
        assert build_scrape_jobs(settings) is None


class _StubRunClient:
    def __init__(
        self, payload: dict[str, Any], *, finish: dict[str, Any] | None = None
    ) -> None:
        self.payload = payload
        self.finish_payload = finish or payload
        self.gets = 0

    async def get(self) -> dict[str, Any]:
        self.gets += 1
        return self.payload if self.gets == 1 else self.finish_payload


class _StubActorClient:
    def __init__(self, versions: list[dict[str, Any]], started: dict[str, Any]) -> None:
        self.versions = versions
        self.started = started
        self.start_calls: list[dict[str, Any]] = []

    async def get(self) -> dict[str, Any]:
        return {"versions": self.versions}

    async def start(self, run_input: dict[str, Any] | None = None) -> dict[str, Any]:
        self.start_calls.append(run_input or {})
        return self.started


class StubApifyClient:
    def __init__(
        self,
        *,
        versions: list[dict[str, Any]] | None = None,
        run_payload: dict[str, Any] | None = None,
        finish_payload: dict[str, Any] | None = None,
    ) -> None:
        self.actor_client = _StubActorClient(
            versions if versions is not None else [{"versionNumber": "0.1.9"}],
            {"id": "run-1"},
        )
        self._run_payload = run_payload or {
            "id": "run-1",
            "status": "RUNNING",
            "startedAt": "2026-09-10T10:00:00.000Z",
        }
        self._finish_payload = finish_payload or {
            "id": "run-1",
            "status": "SUCCEEDED",
            "defaultDatasetId": "ds-1",
            "startedAt": "2026-09-10T10:00:00.000Z",
            "finishedAt": "2026-09-10T10:05:00.000Z",
        }
        self.run_client = _StubRunClient(self._run_payload, finish=self._finish_payload)

    def actor(self, actor_id: str) -> _StubActorClient:
        assert actor_id == "actor-1"
        return self.actor_client

    def run(self, run_id: str) -> _StubRunClient:
        assert run_id == "run-1"
        return self.run_client


def _gateway(client: Any) -> ApifyJobScraperGateway:
    return ApifyJobScraperGateway(token="t", actor_id="actor-1", client=client)


class TestApifyGatewayLifecycle:
    def test_ensure_compatible_returns_deployed_version(self):
        assert run(_gateway(StubApifyClient()).ensure_compatible()) == "0.1.9"

    def test_ensure_compatible_rejects_old_actor(self):
        client = StubApifyClient(versions=[{"versionNumber": "0.1.4"}])
        strict = ApifyJobScraperGateway(
            token="t", actor_id="actor-1", minimum_actor_version="0.2", client=client
        )
        with pytest.raises(UnsupportedActorVersion):
            run(strict.ensure_compatible())

    def test_ensure_compatible_rejects_actor_without_versions(self):
        with pytest.raises(UnsupportedActorVersion):
            run(_gateway(StubApifyClient(versions=[])).ensure_compatible())

    def test_start_run_passes_input(self):
        client = StubApifyClient()
        result = run(_gateway(client).start_run({"searches": []}, key="k"))
        assert result.run_id == "run-1"
        assert client.actor_client.start_calls == [{"searches": []}]

    def test_fetch_status_maps_actor_fields(self):
        result = run(_gateway(StubApifyClient()).fetch_status("run-1"))
        assert result.status is RunStatus.RUNNING
        assert result.started_at is not None

    def test_await_completion_polls_then_reads_final_state(self):
        client = StubApifyClient()
        result = run(
            _gateway(client).await_completion(ScrapeRun.new("run-1"), poll_secs=0.001)
        )
        assert client.run_client.gets >= 2  # polled until terminal
        assert result.status is RunStatus.SUCCEEDED
        assert result.dataset_id == "ds-1"
        assert result.finished_at is not None

    def test_unknown_actor_status_is_not_terminal(self):
        assert RunStatus.from_actor("SOMETHING-NEW") is RunStatus.RUNNING


class TestEventPublishingJobSink:
    def test_publishes_one_event_per_page(self):
        from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
        from agentic_mail_mcp.Jobs.Domain.Events.jobs_scraped import JobsScraped
        from agentic_mail_mcp.Jobs.Infrastructure.Events.event_publishing_job_sink import (
            EventPublishingJobSink,
        )

        bus = InMemoryEventBus()
        sink = EventPublishingJobSink(bus)
        sink.bind("run-9")
        run(sink.ingest_page([{"jobId": "1"}, {"jobId": "2"}]))

        events = [e for e in bus.published if isinstance(e, JobsScraped)]
        assert [(e.run_id, e.count) for e in events] == [("run-9", 2)]

    def test_use_case_binds_run_id_into_sink(self):
        from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
        from agentic_mail_mcp.Jobs.Domain.Events.jobs_scraped import JobsScraped
        from agentic_mail_mcp.Jobs.Infrastructure.Events.event_publishing_job_sink import (
            EventPublishingJobSink,
        )

        bus = InMemoryEventBus()
        sink = EventPublishingJobSink(bus)
        result = run(
            ScrapeJobsUseCase(FakeGateway(), InMemoryRunRepository()).execute(
                {"a": 1}, sink
            )
        )

        counts = [
            (e.run_id, e.count) for e in bus.published if isinstance(e, JobsScraped)
        ]
        assert counts == [(result.run_id, 1), (result.run_id, 2)]


class TestCompositionWiring:
    def test_enabled_flag_builds_use_case(self):
        from agentic_mail_mcp.Bootstrap.Composition import build_scrape_jobs
        from agentic_mail_mcp.Bootstrap.Settings import Settings

        settings = Settings(apify_jobs={"enabled": True, "token": "tok"})
        use_case = build_scrape_jobs(settings)
        assert use_case is not None
