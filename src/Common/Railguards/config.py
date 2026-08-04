from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from src.Common.Domain.Exceptions import ValidationError

READ_ONLY = "read_only"
READ_WRITE = "read_write"
_VALID_ACCESS_LEVELS = frozenset({READ_ONLY, READ_WRITE})


@dataclass(frozen=True)
class RailguardConfig:
    """Railguard policy, built from the Settings.railguards section.

    ``access_level`` is the master switch: ``read_only`` (default) denies every
    write regardless of the other rules.
    """

    access_level: str = READ_ONLY
    allowed_recipients: list[str] = field(default_factory=list)
    blocked_actions: list[str] = field(default_factory=list)
    rate_limits: dict[str, int] = field(default_factory=dict)
    archive_first_policy: bool = False

    def __post_init__(self) -> None:
        if self.access_level not in _VALID_ACCESS_LEVELS:
            raise ValidationError(
                f"access_level must be one of {sorted(_VALID_ACCESS_LEVELS)}, "
                f"got {self.access_level!r}"
            )

    @classmethod
    def from_settings(cls, railguards: Any) -> RailguardConfig:
        return cls(
            access_level=railguards.access_level,
            allowed_recipients=list(railguards.allowed_recipients),
            blocked_actions=list(railguards.blocked_actions),
            rate_limits=dict(railguards.rate_limits),
            archive_first_policy=railguards.archive_first_policy,
        )

    @property
    def is_read_only(self) -> bool:
        return self.access_level == READ_ONLY

    def recipient_allowed(self, address: str) -> bool:
        """True when no allowlist is configured, or the address matches an
        allowed full address or domain (``@example.com``)."""
        if not self.allowed_recipients:
            return True
        address = address.lower()
        domain = address.rsplit("@", 1)[-1]
        for entry in self.allowed_recipients:
            entry = entry.lower()
            if entry.startswith("@"):
                if domain == entry[1:]:
                    return True
            elif entry == address:
                return True
        return False

    def is_action_blocked(self, action: str) -> bool:
        return action in self.blocked_actions

    def rate_limit_for(self, action: str) -> int | None:
        return self.rate_limits.get(action)
