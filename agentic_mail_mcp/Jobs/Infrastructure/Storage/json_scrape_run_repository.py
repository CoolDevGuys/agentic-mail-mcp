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
from pathlib import Path

from agentic_mail_mcp.Jobs.Domain.Model.scrape_run import ScrapeRun

logger = logging.getLogger(__name__)


class JsonScrapeRunRepository:
    def __init__(self, directory: str | Path = "data/scrape_runs") -> None:
        self._directory = Path(directory)

    def _path(self, key: str) -> Path:
        safe = "".join(c if c.isalnum() or c in "-_." else "_" for c in key)
        return self._directory / f"{safe or 'default'}.json"

    def load(self, key: str) -> ScrapeRun | None:
        path = self._path(key)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            return None
        except (json.JSONDecodeError, OSError, KeyError, ValueError, TypeError) as exc:
            # A corrupt record must not block a re-run: treat it as absent.
            logger.warning(
                "Ignoring unreadable scrape run record",
                extra={"path": str(path), "error": str(exc)},
            )
            return None
        if not isinstance(raw, dict):
            return None
        return ScrapeRun.from_dict(raw)

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
