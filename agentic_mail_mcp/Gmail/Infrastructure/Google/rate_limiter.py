from __future__ import annotations

import time
from collections.abc import Callable


class RateLimiter:
    """Minimum-interval rate limiter.

    Ensures successive acquisitions are spaced at least ``1 / max_per_second``
    apart. The clock and sleep functions are injectable for deterministic tests.
    """

    def __init__(
        self,
        max_per_second: float,
        *,
        clock: Callable[[], float] = time.monotonic,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        if max_per_second <= 0:
            raise ValueError("max_per_second must be > 0")
        self._min_interval = 1.0 / max_per_second
        self._clock = clock
        self._sleep = sleep
        self._last: float | None = None

    def acquire(self) -> None:
        now = self._clock()
        if self._last is not None:
            elapsed = now - self._last
            wait = self._min_interval - elapsed
            if wait > 0:
                self._sleep(wait)
                now = self._clock()
        self._last = now
