from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta

from src.Common.Domain.Exceptions import PermissionError
from src.Common.Infrastructure.Clock import Clock, SystemClock
from src.Common.Railguards.config import RailguardConfig

PERMANENT_DELETE = "permanent_delete"


@dataclass(frozen=True)
class RailguardResult:
    allowed: bool
    reason: str = ""


@dataclass(frozen=True)
class RailguardRequest:
    """A backend-agnostic description of a write operation to validate.

    Use cases build this from their command so the validator stays decoupled
    from the Gmail bounded context.
    """

    action: str
    recipient: str | None = None
    is_archived: bool | None = None


class RailguardValidator:
    """Validates write operations against the railguard policy.

    ``check`` returns a RailguardResult without raising; ``validate`` raises
    PermissionError when the operation is denied. Allowed operations are
    recorded against the rate-limit window.
    """

    def __init__(
        self,
        config: RailguardConfig,
        *,
        clock: Clock | None = None,
        window_seconds: int = 3600,
    ) -> None:
        self._config = config
        self._clock = clock or SystemClock()
        self._window = timedelta(seconds=window_seconds)
        self._history: dict[str, list[datetime]] = defaultdict(list)

    def check(self, request: RailguardRequest) -> RailguardResult:
        if self._config.is_read_only:
            return RailguardResult(False, "access level is read_only; writes denied")

        if self._config.is_action_blocked(request.action):
            return RailguardResult(False, f"action {request.action!r} is blocked")

        if (
            request.action == "forward"
            and request.recipient is not None
            and not self._config.recipient_allowed(request.recipient)
        ):
            return RailguardResult(
                False, f"recipient {request.recipient!r} is not allowed"
            )

        if (
            request.action == PERMANENT_DELETE
            and self._config.archive_first_policy
            and request.is_archived is False
        ):
            return RailguardResult(
                False, "archive-first policy: email must be archived before delete"
            )

        limit = self._config.rate_limit_for(request.action)
        if limit is not None and self._count_in_window(request.action) >= limit:
            return RailguardResult(
                False, f"rate limit exceeded for {request.action!r}"
            )

        return RailguardResult(True)

    def validate(self, request: RailguardRequest) -> RailguardResult:
        result = self.check(request)
        if not result.allowed:
            raise PermissionError(result.reason)
        # A rate-limit slot is reserved at validation time, before the caller
        # performs the operation. A subsequent gateway failure still consumes the
        # slot; this is intentional so retries of a failing action cannot bypass
        # the limit.
        self._record(request.action)
        return result

    def _count_in_window(self, action: str) -> int:
        cutoff = self._clock.now() - self._window
        recent = [ts for ts in self._history[action] if ts >= cutoff]
        self._history[action] = recent
        return len(recent)

    def _record(self, action: str) -> None:
        if self._config.rate_limit_for(action) is not None:
            self._history[action].append(self._clock.now())
