from __future__ import annotations

import time
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")

_TRANSIENT_STATUSES = frozenset({429, 500, 502, 503, 504})


def _status_of(error: Exception) -> int | None:
    # googleapiclient.errors.HttpError exposes .resp.status; be defensive.
    resp = getattr(error, "resp", None)
    status = getattr(resp, "status", None)
    if status is None:
        status = getattr(error, "status_code", None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


def retry_on_transient(
    operation: Callable[[], T],
    *,
    max_attempts: int = 3,
    backoff_base: float = 0.5,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call ``operation``, retrying on transient HTTP errors with backoff."""
    attempt = 0
    while True:
        try:
            return operation()
        except Exception as error:
            status = _status_of(error)
            attempt += 1
            if status not in _TRANSIENT_STATUSES or attempt >= max_attempts:
                raise
            sleep(backoff_base * (2 ** (attempt - 1)))
