from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.thread import Thread
from src.Gmail.Domain.ValueObjects import ThreadId


class TestThreadCreation:
    def test_create_with_emails(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
            subject="Test Subject",
        )

        assert thread.thread_id.value == "thread_1"
        assert thread.subject == "Test Subject"
        assert thread.email_ids == (email_id,)
        assert thread.is_read is False
        assert thread.last_updated is not None

    def test_create_empty_rejected(self) -> None:
        with pytest.raises(ValidationError, match="must contain at least one email"):
            Thread.create(
                thread_id=ThreadId(value="thread_1"),
                email_ids=[],
            )

    def test_create_with_default_values(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_2"),
            email_ids=[email_id],
        )

        assert thread.subject == ""
        assert thread.snippet == ""
        assert thread.participants == []


class TestThreadBehaviors:
    def test_add_email(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
        )

        new_email = UUIDId.generate()
        thread.add_email(new_email)

        assert new_email in thread.email_ids
        assert len(thread.email_ids) == 2

    def test_add_email_sorted_by_date(self) -> None:
        mid_email = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[mid_email],
        )

        earlier = datetime(2020, 1, 1, tzinfo=UTC)
        later = datetime(2030, 12, 31, tzinfo=UTC)
        earlier_email = UUIDId.generate()
        later_email = UUIDId.generate()

        thread.add_email(later_email, date_sent=later)
        thread.add_email(earlier_email, date_sent=earlier)

        assert thread.email_ids == (earlier_email, mid_email, later_email)

    def test_add_email_updates_timestamp(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
        )
        original_updated = thread.last_updated

        thread.add_email(UUIDId.generate())

        assert thread.last_updated is not None

    def test_mark_read(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
        )

        assert thread.is_read is False
        thread.mark_read()
        assert thread.is_read is True


class TestThreadInvariants:
    def test_emails_not_duplicated(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
        )

        thread.add_email(email_id)

        assert thread.email_ids.count(email_id) == 1

    def test_email_ids_returns_tuple(self) -> None:
        email_id = UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=[email_id],
        )

        assert isinstance(thread.email_ids, tuple)

    def test_non_empty_on_creation(self) -> None:
        with pytest.raises(ValidationError):
            Thread.create(
                thread_id=ThreadId(value="thread_1"),
                email_ids=[],
            )

    def test_create_with_multiple_emails(self) -> None:
        email_ids = [UUIDId.generate() for _ in range(3)]
        thread = Thread.create(
            thread_id=ThreadId(value="thread_1"),
            email_ids=email_ids,
        )

        assert len(thread.email_ids) == 3
        for eid in email_ids:
            assert eid in thread.email_ids
