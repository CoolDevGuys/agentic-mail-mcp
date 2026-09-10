"""Filesystem-backed scrape run records.

The integration runs inside a short-lived process (MCP server or CLI command),
so run lifecycle only needs to survive a crash between trigger and completion.
A single JSON file per run key is enough, and keeps the port free of a database
dependency. Writes are atomic: a crash mid-save leaves the previous record.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime
from pathlib import Path

from agentic_mail_mcp.Jobs.Domain.Model.scrape_run import ScrapeRun

logger = logging.getLogger(__name__)


CLAIM_STALE_SECS = 120.0


class JsonScrapeRunRepository:
    def __init__(
        self,
        directory: str | Path = "data/scrape_runs",
        *,
        claim_stale_secs: float = CLAIM_STALE_SECS,
    ) -> None:
        self._directory = Path(directory)
        self._claim_stale_secs = claim_stale_secs

    def _path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self._directory / f"{safe or 'default'}.json"

    def claim(self, key: str) -> bool:
        """Reserve a key before triggering a run (guards concurrent starters).

        A fresh "starting" claim by another process returns False. A stale one
        (crashed starter) is replaced. Residual race window: between claiming
        and the gateway returning the run id, a millisecond-wide crash can
        orphan an already-started run (bounded by maxRunSeconds); the spec's
        crash window it optimizes for is the minutes-long wait, where the
        run id IS persisted before waiting.
        """
        self._directory.mkdir(parents=True, exist_ok=True)
        path = self._path(key)
        placeholder = {"status": "starting", "claimedAt": datetime.now(UTC).isoformat()}
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            return self._reclaim_stale(path, placeholder)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(placeholder, handle)
        except OSError:
            return False
        return True

    def _reclaim_stale(self, path: Path, placeholder: dict[str, str]) -> bool:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = None
        if not isinstance(raw, dict) or raw.get("status") != "starting":
            return False  # a real record exists: caller must attach, not re-claim
        claimed_at = ScrapeRun.parse_timestamp(raw.get("claimedAt"))
        if claimed_at is None:
            return False
        age = (datetime.now(UTC) - claimed_at).total_seconds()
        if age > self._claim_stale_secs:
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(placeholder), encoding="utf-8")
            os.replace(tmp, path)
            return True
        return False

    def load(self, key: str) -> ScrapeRun | None:
        path = self._path(key)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, dict):
                return None
            if raw.get("status") == "starting":
                return None  # starter claim without a run id yet: not a record
            return ScrapeRun.from_dict(raw)
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, OSError, KeyError, ValueError, TypeError) as exc:
            # A corrupt record must not block a re-run: treat it as absent.
            logger.warning(
                "Ignoring unreadable scrape run record",
                extra={"path": str(path), "error": str(exc)},
            )
            return None

    def save(self, run: ScrapeRun) -> None:
        path = self._path(run.key)
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.parent / f"{path.name}.tmp"
        try:
            with tmp.open("w", encoding="utf-8") as handle:
                json.dump(run.to_dict(), handle, sort_keys=True)
            os.replace(tmp, path)
        except OSError:
            tmp.unlink(missing_ok=True)
            raise

    def clear(self, key: str) -> None:
        try:
            self._path(key).unlink()
        except FileNotFoundError:
            return
