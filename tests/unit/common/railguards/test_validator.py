from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.Common.Domain.Exceptions import PermissionError
from src.Common.Infrastructure.Clock import FrozenClock
from src.Common.Railguards.config import RailguardConfig
from src.Common.Railguards.validator import RailguardRequest, RailguardValidator


def _rw(**kw) -> RailguardConfig:
    return RailguardConfig(access_level="read_write", **kw)


class TestReadOnlyMasterSwitch:
    def test_read_only_denies_all_writes(self) -> None:
        validator = RailguardValidator(RailguardConfig())  # default read_only
        result = validator.check(RailguardRequest(action="archive"))
        assert result.allowed is False
        with pytest.raises(PermissionError):
            validator.validate(RailguardRequest(action="archive"))

    def test_read_write_allows_when_no_rule_violated(self) -> None:
        validator = RailguardValidator(_rw())
        assert validator.validate(RailguardRequest(action="archive")).allowed is True


class TestRecipientAllowlist:
    def test_recipient_not_allowed_denied(self) -> None:
        validator = RailguardValidator(_rw(allowed_recipients=["@corp.com"]))
        with pytest.raises(PermissionError):
            validator.validate(
                RailguardRequest(action="forward", recipient="x@evil.com")
            )

    def test_recipient_allowed(self) -> None:
        validator = RailguardValidator(_rw(allowed_recipients=["@corp.com"]))
        assert validator.validate(
            RailguardRequest(action="forward", recipient="a@corp.com")
        ).allowed

    def test_empty_allowlist_does_not_restrict(self) -> None:
        validator = RailguardValidator(_rw())
        assert validator.check(
            RailguardRequest(action="forward", recipient="a@b.com")
        ).allowed


class TestActionBlocklist:
    def test_blocked_action_denied(self) -> None:
        validator = RailguardValidator(_rw(blocked_actions=["permanent_delete"]))
        with pytest.raises(PermissionError):
            validator.validate(RailguardRequest(action="permanent_delete"))


class TestRateLimits:
    def test_rate_limit_exceeded_denied(self) -> None:
        clock = FrozenClock()
        clock.set(datetime(2026, 8, 4, 12, 0, tzinfo=UTC))
        validator = RailguardValidator(_rw(rate_limits={"forward": 2}), clock=clock)
        validator.validate(RailguardRequest(action="forward", recipient="a@b.com"))
        validator.validate(RailguardRequest(action="forward", recipient="a@b.com"))
        with pytest.raises(PermissionError):
            validator.validate(RailguardRequest(action="forward", recipient="a@b.com"))

    def test_operations_outside_window_do_not_count(self) -> None:
        clock = FrozenClock()
        clock.set(datetime(2026, 8, 4, 12, 0, tzinfo=UTC))
        validator = RailguardValidator(
            _rw(rate_limits={"forward": 1}), clock=clock, window_seconds=3600
        )
        validator.validate(RailguardRequest(action="forward", recipient="a@b.com"))
        # Move the clock beyond the window; the earlier op no longer counts.
        clock.set(datetime(2026, 8, 4, 13, 30, tzinfo=UTC))
        assert validator.validate(
            RailguardRequest(action="forward", recipient="a@b.com")
        ).allowed

    def test_unlimited_action_is_not_recorded(self) -> None:
        validator = RailguardValidator(_rw())
        for _ in range(10):
            validator.validate(RailguardRequest(action="archive"))


class TestArchiveFirst:
    def test_permanent_delete_of_non_archived_denied(self) -> None:
        validator = RailguardValidator(_rw(archive_first_policy=True))
        with pytest.raises(PermissionError):
            validator.validate(
                RailguardRequest(action="permanent_delete", is_archived=False)
            )

    def test_permanent_delete_of_archived_allowed(self) -> None:
        validator = RailguardValidator(_rw(archive_first_policy=True))
        assert validator.validate(
            RailguardRequest(action="permanent_delete", is_archived=True)
        ).allowed

    def test_archive_first_disabled_allows_non_archived(self) -> None:
        validator = RailguardValidator(_rw(archive_first_policy=False))
        assert validator.check(
            RailguardRequest(action="permanent_delete", is_archived=False)
        ).allowed
