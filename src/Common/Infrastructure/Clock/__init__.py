from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """Protocol for obtaining the current time."""

    def now(self) -> datetime: ...


class SystemClock:
    """Returns the current UTC-aware datetime."""

    def now(self) -> datetime:
        return datetime.now(UTC)


class FrozenClock:
    """Injectable clock for deterministic tests."""

    def __init__(self) -> None:
        self._frozen: datetime | None = None

    def now(self) -> datetime:
        if self._frozen is not None:
            return self._frozen
        return datetime.now(UTC)

    def set(self, dt: datetime) -> None:
        self._frozen = dt

    def unfreeze(self) -> None:
        self._frozen = None
