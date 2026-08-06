from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Notification.Domain.Events import (
    DigestReady,
    ImportantEmailDetected,
    InboxChanged,
)


class TestImportantEmailDetected:
    def test_creation_sets_all_fields(self) -> None:
        email_id = UUIDId.generate()
        event = ImportantEmailDetected(
            email_id=email_id,
            from_address="sender@example.com",
            subject="Important Update",
            priority=3,
        )

        assert event.email_id == email_id
        assert event.from_address == "sender@example.com"
        assert event.subject == "Important Update"
        assert event.priority == 3
        assert isinstance(event.detected_at, datetime)
        assert event.detected_at.tzinfo is not None

    def test_priority_valid_range_accepted(self) -> None:
        for priority in (1, 3, 5):
            event = ImportantEmailDetected(
                email_id=UUIDId.generate(),
                from_address="test@example.com",
                subject="Test",
                priority=priority,
            )
            assert event.priority == priority

    def test_priority_below_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="priority must be between 1 and 5"):
            ImportantEmailDetected(
                email_id=UUIDId.generate(),
                from_address="test@example.com",
                subject="Test",
                priority=0,
            )

    def test_priority_above_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="priority must be between 1 and 5"):
            ImportantEmailDetected(
                email_id=UUIDId.generate(),
                from_address="test@example.com",
                subject="Test",
                priority=6,
            )

    def test_detected_at_defaults_to_utc(self) -> None:
        event = ImportantEmailDetected(
            email_id=UUIDId.generate(),
            from_address="test@example.com",
            subject="Test",
            priority=1,
        )

        assert event.detected_at.tzinfo == UTC

    def test_detected_at_can_be_overridden(self) -> None:
        custom_time = datetime(2024, 6, 15, 12, 0, 0, tzinfo=UTC)
        event = ImportantEmailDetected(
            email_id=UUIDId.generate(),
            from_address="test@example.com",
            subject="Test",
            priority=1,
            detected_at=custom_time,
        )

        assert event.detected_at == custom_time


class TestInboxChanged:
    def test_creation_sets_all_fields(self) -> None:
        email_id = UUIDId.generate()
        event = InboxChanged(
            event_type="added",
            email_id=email_id,
        )

        assert event.event_type == "added"
        assert event.email_id == email_id
        assert isinstance(event.changed_at, datetime)
        assert event.changed_at.tzinfo is not None

    def test_changed_at_defaults_to_utc(self) -> None:
        event = InboxChanged(
            event_type="removed",
            email_id=UUIDId.generate(),
        )

        assert event.changed_at.tzinfo == UTC

    def test_changed_at_can_be_overridden(self) -> None:
        custom_time = datetime(2024, 1, 1, 0, 0, 0, tzinfo=UTC)
        event = InboxChanged(
            event_type="updated",
            email_id=UUIDId.generate(),
            changed_at=custom_time,
        )

        assert event.changed_at == custom_time

    def test_event_type_variants(self) -> None:
        for event_type in ("added", "removed", "updated"):
            event = InboxChanged(
                event_type=event_type,
                email_id=UUIDId.generate(),
            )
            assert event.event_type == event_type


class TestDigestReady:
    def test_creation_with_valid_digest_type(self) -> None:
        event = DigestReady(
            digest_type="daily",
            digest_period="2024-08-01",
            email_count=5,
        )

        assert event.digest_type == "daily"
        assert event.digest_period == "2024-08-01"
        assert event.email_count == 5
        assert isinstance(event.generated_at, datetime)
        assert event.generated_at.tzinfo is not None

    def test_weekly_digest_type_accepted(self) -> None:
        event = DigestReady(
            digest_type="weekly",
            digest_period="2024-W31",
            email_count=20,
        )

        assert event.digest_type == "weekly"

    def test_invalid_digest_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="digest_type must be one of"):
            DigestReady(
                digest_type="monthly",
                digest_period="2024-08",
                email_count=10,
            )

    def test_generated_at_defaults_to_utc(self) -> None:
        event = DigestReady(
            digest_type="daily",
            digest_period="2024-08-01",
            email_count=0,
        )

        assert event.generated_at.tzinfo == UTC

    def test_generated_at_can_be_overridden(self) -> None:
        custom_time = datetime(2024, 8, 1, 6, 0, 0, tzinfo=UTC)
        event = DigestReady(
            digest_type="daily",
            digest_period="2024-08-01",
            email_count=3,
            generated_at=custom_time,
        )

        assert event.generated_at == custom_time

    def test_zero_email_count_is_valid(self) -> None:
        event = DigestReady(
            digest_type="daily",
            digest_period="2024-08-01",
            email_count=0,
        )

        assert event.email_count == 0
