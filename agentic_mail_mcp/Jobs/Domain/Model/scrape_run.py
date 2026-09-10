"""Domain model for an actor-driven job-scrape run."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum


def _as_opt_str(value: object) -> str | None:
    return str(value) if value is not None else None


class RunStatus(str, Enum):
    """Scrape run lifecycle, mapped from the underlying actor run state."""

    PENDING = "pending"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ABORTED = "aborted"
    TIMED_OUT = "timed_out"

    @property
    def is_terminal(self) -> bool:
        return self in (
            RunStatus.SUCCEEDED,
            RunStatus.FAILED,
            RunStatus.ABORTED,
            RunStatus.TIMED_OUT,
        )

    @classmethod
    def from_actor(cls, value: str) -> RunStatus:
        """Map an actor run status string onto the domain enum.

        Unknown values map to RUNNING (non-terminal): an unrecognized state
        must never be mistaken for completion.
        """
        try:
            return cls(value.strip().lower().replace("-", "_"))
        except ValueError:
            return cls.RUNNING


@dataclass(frozen=True)
class ScrapeRun:
    """A single scrape run: an actor run id plus the state the integration needs
    to re-attach after an interruption instead of double-triggering."""

    run_id: str
    status: RunStatus = RunStatus.PENDING
    dataset_id: str | None = None
    key: str = "default"
    started_at: datetime | None = None
    finished_at: datetime | None = None
    items_ingested: int = 0

    @classmethod
    def new(cls, run_id: str, key: str = "default") -> ScrapeRun:
        return cls(
            run_id=run_id,
            key=key,
            status=RunStatus.RUNNING,
            started_at=datetime.now(UTC),
        )

    @staticmethod
    def parse_timestamp(value: str | None) -> datetime | None:
        if not value:
            return None
        try:
            return datetime.fromisoformat(value)
        except ValueError:
            return None

    def to_dict(self) -> dict[str, object]:
        return {
            "run_id": self.run_id,
            "status": self.status.value,
            "dataset_id": self.dataset_id,
            "key": self.key,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "items_ingested": self.items_ingested,
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> ScrapeRun:
        raw_status = str(data.get("status") or RunStatus.PENDING.value)
        # Unknown values fall back to RUNNING via from_actor (non-terminal):
        # a status we cannot read must never be trusted as completion.
        return cls(
            run_id=str(data["run_id"]),
            status=RunStatus.from_actor(raw_status),
            dataset_id=(str(v) if (v := data.get("dataset_id")) else None),
            key=str(data.get("key") or "default"),
            started_at=cls.parse_timestamp(_as_opt_str(data.get("started_at"))),
            finished_at=cls.parse_timestamp(_as_opt_str(data.get("finished_at"))),
            items_ingested=int(str(data.get("items_ingested") or 0)),
        )
