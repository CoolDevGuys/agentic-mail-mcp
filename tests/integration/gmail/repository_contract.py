"""Backend-agnostic contract tests for the Gmail repository ports.

Subclasses provide an ``email_repo`` / ``thread_repo`` fixture bound to a
concrete backend (SQLite, PostgreSQL, ...). The same assertions must hold for
every implementation, guaranteeing interchangeability.
"""

from __future__ import annotations

from datetime import UTC, datetime

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Entities.thread import Thread
from src.Gmail.Domain.ValueObjects import ThreadId


def _make_email(message_id: str, *, read: bool = False, subject: str = "Hello") -> Email:
    email = Email.from_gmail_message(
        message_id=message_id,
        thread_id="thread_1",
        subject=subject,
        from_address="sender@example.com",
        to_addresses=["r@example.com"],
        body="Body text",
    )
    email.date_sent = datetime(2026, 1, 1, tzinfo=UTC)
    if read:
        email.mark_read()
    return email


class EmailRepositoryContractTests:
    def test_save_and_find_by_id(self, email_repo) -> None:
        email = _make_email("m1")
        email_repo.save(email)
        found = email_repo.find_by_id(email.id)
        assert found is not None
        assert found.message_id.value == "m1"
        assert found.subject == "Hello"

    def test_find_by_gmail_message_id(self, email_repo) -> None:
        email = _make_email("m2")
        email_repo.save(email)
        found = email_repo.find_by_gmail_message_id("m2")
        assert found is not None
        assert found.id == email.id

    def test_find_by_thread_id(self, email_repo) -> None:
        email_repo.save(_make_email("m3"))
        email_repo.save(_make_email("m4"))
        found = email_repo.find_by_thread_id("thread_1")
        assert {e.message_id.value for e in found} == {"m3", "m4"}

    def test_missing_email_returns_none(self, email_repo) -> None:
        assert email_repo.find_by_id(UUIDId.generate()) is None
        assert email_repo.find_by_gmail_message_id("nope") is None

    def test_list_unread_respects_limit(self, email_repo) -> None:
        for i in range(5):
            email_repo.save(_make_email(f"u{i}"))
        assert len(email_repo.list_unread(limit=3)) == 3

    def test_list_unread_excludes_read(self, email_repo) -> None:
        email_repo.save(_make_email("unread1"))
        email_repo.save(_make_email("read1", read=True))
        unread = email_repo.list_unread(limit=10)
        assert [e.message_id.value for e in unread] == ["unread1"]

    def test_search_matches_subject(self, email_repo) -> None:
        email_repo.save(_make_email("s1", subject="Invoice March"))
        email_repo.save(_make_email("s2", subject="Lunch plans"))
        results = email_repo.search("Invoice")
        assert [e.message_id.value for e in results] == ["s1"]

    def test_save_is_upsert(self, email_repo) -> None:
        email = _make_email("up1")
        email_repo.save(email)
        email.mark_read()
        email_repo.save(email)
        found = email_repo.find_by_id(email.id)
        assert found.is_read is True

    def test_delete_removes_email(self, email_repo) -> None:
        email = _make_email("d1")
        email_repo.save(email)
        email_repo.delete(email.id)
        assert email_repo.find_by_id(email.id) is None


class ThreadRepositoryContractTests:
    def test_save_and_find_by_gmail_thread_id(self, thread_repo) -> None:
        e1, e2 = UUIDId.generate(), UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId("t1"), email_ids=[e1, e2], subject="Subj"
        )
        thread_repo.save(thread)
        found = thread_repo.find_by_gmail_thread_id("t1")
        assert found is not None
        assert found.subject == "Subj"
        assert found.email_ids == (e1, e2)

    def test_find_by_id(self, thread_repo) -> None:
        thread = Thread.create(thread_id=ThreadId("t2"), email_ids=[UUIDId.generate()])
        thread_repo.save(thread)
        assert thread_repo.find_by_id(thread.id) is not None

    def test_missing_thread_returns_none(self, thread_repo) -> None:
        assert thread_repo.find_by_gmail_thread_id("missing") is None
        assert thread_repo.find_by_id(UUIDId.generate()) is None

    def test_delete_removes_thread(self, thread_repo) -> None:
        thread = Thread.create(thread_id=ThreadId("t3"), email_ids=[UUIDId.generate()])
        thread_repo.save(thread)
        thread_repo.delete(thread.id)
        assert thread_repo.find_by_id(thread.id) is None
