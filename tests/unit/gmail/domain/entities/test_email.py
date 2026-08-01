from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.Common.Domain.Exceptions import DomainError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Events import (
    EmailArchived,
    EmailDeleted,
    EmailLabeled,
    EmailRead,
)
from src.Gmail.Domain.ValueObjects import EmailAddress, GmailMessageId, ThreadId


class TestEmailFactory:
    def test_from_gmail_message_creates_email(self) -> None:
        email = Email.from_gmail_message(
            message_id="msg_1",
            thread_id="thread_1",
            subject="Hello",
            from_address="sender@example.com",
            to_addresses=["recipient@example.com"],
        )

        assert isinstance(email.id, UUIDId)
        assert email.message_id == GmailMessageId("msg_1")
        assert email.thread_id == ThreadId("thread_1")
        assert email.subject == "Hello"
        assert email.from_address == EmailAddress("sender@example.com")
        assert email.to_addresses == [EmailAddress("recipient@example.com")]
        assert email.snippet == ""
        assert email.body == ""
        assert email.is_read is False
        assert email.is_trashed is False

    def test_from_gmail_message_with_labels(self) -> None:
        email = Email.from_gmail_message(
            message_id="msg_1",
            thread_id="thread_1",
            labels=["Important", "Work"],
        )

        assert email.labels == frozenset({"Important", "Work"})

    def test_from_gmail_message_with_date_sent(self) -> None:
        dt = datetime(2024, 1, 15, 10, 30, 0, tzinfo=UTC)
        email = Email.from_gmail_message(
            message_id="msg_1",
            thread_id="thread_1",
            date_sent=dt,
        )

        assert email.date_sent == dt

    def test_from_gmail_message_without_from_address(self) -> None:
        email = Email.from_gmail_message(
            message_id="msg_1",
            thread_id="thread_1",
        )

        assert email.from_address is None
        assert email.to_addresses == []


class TestEmailBehaviors:
    def test_mark_read_once(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        assert email.is_read is False

        email.mark_read()
        assert email.is_read is True

    def test_mark_read_emits_event(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.mark_read()

        events = email.domain_events
        assert len(events) == 1
        assert isinstance(events[0], EmailRead)
        assert events[0].email_id == email.id

    def test_mark_read_idempotent(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.is_read = True

        email.mark_read()
        assert email.is_read is True

    def test_add_label(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.add_label("Important")

        assert "Important" in email.labels

    def test_remove_label(self) -> None:
        email = Email.from_gmail_message(
            "msg_1", "thread_1", labels=["Important"]
        )
        email.remove_label("Important")

        assert "Important" not in email.labels

    def test_remove_nonexistent_label(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.remove_label("NonExistent")

        assert email.labels == frozenset()

    def test_archive(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.archive()

        events = email.domain_events
        assert len(events) == 1
        assert isinstance(events[0], EmailArchived)

    def test_move_to_trash(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        assert email.is_trashed is False

        email.move_to_trash()
        assert email.is_trashed is True

    def test_restore_from_trash(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.move_to_trash()
        assert email.is_trashed is True

        email.restore_from_trash()
        assert email.is_trashed is False


class TestEmailInvariants:
    def test_labels_are_unique(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1", labels=["Work"])
        email.add_label("Work")
        email.add_label("Work")

        assert email.labels == frozenset({"Work"})

    def test_labels_property_returns_frozenset(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1", labels=["Work"])
        assert isinstance(email.labels, frozenset)

    def test_restore_fails_for_non_trashed_email(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")

        with pytest.raises(DomainError, match="Cannot restore"):
            email.restore_from_trash()

    def test_attachments_property_returns_copy(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email._attachments.append("file1.pdf")
        attachments = email.attachments
        attachments.append("file2.pdf")

        assert email.attachments == ["file1.pdf"]


class TestEmailDomainEvents:
    def test_add_label_emits_event(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.add_label("Important")

        events = email.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, EmailLabeled)
        assert event.email_id == email.id
        assert event.label_name == "Important"

    def test_add_duplicate_label_no_event(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1", labels=["Important"])
        email.add_label("Important")

        assert len(email.domain_events) == 0

    def test_archive_emits_event(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.archive()

        events = email.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, EmailArchived)
        assert event.email_id == email.id

    def test_move_to_trash_emits_event(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.move_to_trash()

        events = email.domain_events
        assert len(events) == 1
        event = events[0]
        assert isinstance(event, EmailDeleted)
        assert event.email_id == email.id

    def test_domain_events_cleared_after_read(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.add_label("Work")

        events1 = email.domain_events
        assert len(events1) == 1

        events2 = email.domain_events
        assert len(events2) == 0

    def test_multiple_events_accumulated(self) -> None:
        email = Email.from_gmail_message("msg_1", "thread_1")
        email.add_label("Work")
        email.add_label("Personal")
        email.archive()

        events = email.domain_events
        assert len(events) == 3
        assert isinstance(events[0], EmailLabeled)
        assert isinstance(events[1], EmailLabeled)
        assert isinstance(events[2], EmailArchived)
