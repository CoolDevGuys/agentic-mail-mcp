from __future__ import annotations

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Entities.thread import Thread
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Gmail.Domain.Repository.thread_repository import ThreadRepository


class FakeEmailRepository:
    def __init__(self) -> None:
        self._store: dict[UUIDId, Email] = {}

    def find_by_id(self, id: UUIDId) -> Email | None:
        return self._store.get(id)

    def find_by_gmail_message_id(self, message_id: str) -> Email | None:
        for email in self._store.values():
            if email.message_id.value == message_id:
                return email
        return None

    def find_by_thread_id(self, thread_id: str) -> list[Email]:
        return [e for e in self._store.values() if e.thread_id.value == thread_id]

    def search(self, query: str) -> list[Email]:
        return [e for e in self._store.values() if query.lower() in e.subject.lower()]

    def list_unread(self, limit: int) -> list[Email]:
        unread = [e for e in self._store.values() if not e.is_read]
        return unread[:limit]

    def save(self, email: Email) -> None:
        self._store[email.id] = email

    def delete(self, id: UUIDId) -> None:
        self._store.pop(id, None)


class FakeThreadRepository:
    def __init__(self) -> None:
        self._store: dict[UUIDId, Thread] = {}

    def find_by_id(self, id: UUIDId) -> Thread | None:
        return self._store.get(id)

    def find_by_gmail_thread_id(self, thread_id: str) -> Thread | None:
        for thread in self._store.values():
            if thread.thread_id.value == thread_id:
                return thread
        return None

    def save(self, thread: Thread) -> None:
        self._store[thread.id] = thread

    def delete(self, id: UUIDId) -> None:
        self._store.pop(id, None)


class TestEmailRepositoryProtocol:
    def test_fake_implements_protocol(self) -> None:
        repo = FakeEmailRepository()
        assert isinstance(repo, EmailRepository)

    def test_find_by_id_returns_email(self) -> None:
        repo = FakeEmailRepository()
        email = Email.from_gmail_message("msg_1", "thread_1", subject="Test")
        repo.save(email)

        result = repo.find_by_id(email.id)
        assert result is not None
        assert result.id == email.id

    def test_find_by_id_returns_none(self) -> None:
        repo = FakeEmailRepository()
        result = repo.find_by_id(UUIDId.generate())
        assert result is None

    def test_find_by_gmail_message_id(self) -> None:
        repo = FakeEmailRepository()
        email = Email.from_gmail_message("msg_1", "thread_1")
        repo.save(email)

        result = repo.find_by_gmail_message_id("msg_1")
        assert result is not None
        assert result.id == email.id

    def test_find_by_thread_id(self) -> None:
        repo = FakeEmailRepository()
        email1 = Email.from_gmail_message("msg_1", "thread_1")
        email2 = Email.from_gmail_message("msg_2", "thread_1")
        email3 = Email.from_gmail_message("msg_3", "thread_2")
        repo.save(email1)
        repo.save(email2)
        repo.save(email3)

        results = repo.find_by_thread_id("thread_1")
        assert len(results) == 2

    def test_search_by_subject(self) -> None:
        repo = FakeEmailRepository()
        email = Email.from_gmail_message("msg_1", "thread_1", subject="Hello World")
        repo.save(email)

        results = repo.search("hello")
        assert len(results) == 1

    def test_list_unread(self) -> None:
        repo = FakeEmailRepository()
        email1 = Email.from_gmail_message("msg_1", "thread_1")
        email2 = Email.from_gmail_message("msg_2", "thread_1")
        email2.is_read = True
        repo.save(email1)
        repo.save(email2)

        results = repo.list_unread(10)
        assert len(results) == 1
        assert results[0].id == email1.id

    def test_delete(self) -> None:
        repo = FakeEmailRepository()
        email = Email.from_gmail_message("msg_1", "thread_1")
        repo.save(email)
        repo.delete(email.id)

        assert repo.find_by_id(email.id) is None

    def test_protocol_methods_exist(self) -> None:
        repo: EmailRepository = FakeEmailRepository()
        assert callable(repo.find_by_id)
        assert callable(repo.find_by_gmail_message_id)
        assert callable(repo.find_by_thread_id)
        assert callable(repo.search)
        assert callable(repo.list_unread)
        assert callable(repo.save)
        assert callable(repo.delete)


class TestThreadRepositoryProtocol:
    def test_fake_implements_protocol(self) -> None:
        repo = FakeThreadRepository()
        assert isinstance(repo, ThreadRepository)

    def test_save_and_find_by_id(self) -> None:
        repo = FakeThreadRepository()
        from src.Gmail.Domain.ValueObjects import ThreadId

        thread = Thread.create(
            thread_id=ThreadId("thread_1"),
            email_ids=[UUIDId.generate()],
        )
        repo.save(thread)

        result = repo.find_by_id(thread.id)
        assert result is not None
        assert result.id == thread.id

    def test_find_by_id_returns_none(self) -> None:
        repo = FakeThreadRepository()
        result = repo.find_by_id(UUIDId.generate())
        assert result is None

    def test_find_by_gmail_thread_id(self) -> None:
        repo = FakeThreadRepository()
        from src.Gmail.Domain.ValueObjects import ThreadId

        thread = Thread.create(
            thread_id=ThreadId("thread_1"),
            email_ids=[UUIDId.generate()],
        )
        repo.save(thread)

        result = repo.find_by_gmail_thread_id("thread_1")
        assert result is not None
        assert result.id == thread.id

    def test_delete(self) -> None:
        repo = FakeThreadRepository()
        from src.Gmail.Domain.ValueObjects import ThreadId

        thread = Thread.create(
            thread_id=ThreadId("thread_1"),
            email_ids=[UUIDId.generate()],
        )
        repo.save(thread)
        repo.delete(thread.id)

        assert repo.find_by_id(thread.id) is None

    def test_protocol_methods_exist(self) -> None:
        repo: ThreadRepository = FakeThreadRepository()
        assert callable(repo.find_by_id)
        assert callable(repo.find_by_gmail_thread_id)
        assert callable(repo.save)
        assert callable(repo.delete)
