from datetime import UTC, datetime

from agentic_mail_mcp.Common.Infrastructure.Clock import FrozenClock, SystemClock


class TestSystemClock:
    def test_returns_datetime(self) -> None:
        clock = SystemClock()
        result = clock.now()
        assert isinstance(result, datetime)

    def test_returns_utc(self) -> None:
        clock = SystemClock()
        result = clock.now()
        assert result.tzinfo == UTC


class TestFrozenClock:
    def test_returns_set_time(self) -> None:
        clock = FrozenClock()
        fixed = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
        clock.set(fixed)
        assert clock.now() == fixed

    def test_time_advancement(self) -> None:
        clock = FrozenClock()
        t1 = datetime(2025, 1, 1, tzinfo=UTC)
        t2 = datetime(2025, 6, 1, tzinfo=UTC)
        clock.set(t1)
        assert clock.now() == t1
        clock.set(t2)
        assert clock.now() == t2

    def test_unfreeze(self) -> None:
        clock = FrozenClock()
        fixed = datetime(2025, 1, 1, tzinfo=UTC)
        clock.set(fixed)
        clock.unfreeze()
        assert clock.now() != fixed

    def test_default_returns_current_time(self) -> None:
        clock = FrozenClock()
        result = clock.now()
        assert isinstance(result, datetime)
