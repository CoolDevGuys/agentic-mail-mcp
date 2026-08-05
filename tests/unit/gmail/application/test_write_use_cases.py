from __future__ import annotations

import pytest

from src.Common.Domain.Events import InMemoryEventBus
from src.Common.Domain.Exceptions import PermissionError
from src.Common.Railguards.config import RailguardConfig
from src.Common.Railguards.validator import RailguardValidator
from src.Gmail.Application.Commands.commands import (
    ArchiveEmailCommand,
    CreateDraftCommand,
    DeleteEmailCommand,
    ForwardEmailCommand,
    SendDraftCommand,
)
from src.Gmail.Application.UseCases.archive_email import ArchiveEmailUseCase
from src.Gmail.Application.UseCases.delete_email import DeleteEmailUseCase
from src.Gmail.Application.UseCases.drafts import (
    CreateDraftUseCase,
    SendDraftUseCase,
)
from src.Gmail.Application.UseCases.forward_email import ForwardEmailUseCase
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Events import EmailArchived, EmailDeleted, EmailForwarded
from tests.fakes.ports import InMemoryEmailRepository, StubGmailGateway


def _validator(**kw) -> RailguardValidator:
    return RailguardValidator(RailguardConfig(access_level="read_write", **kw))


def _email(message_id: str = "m1", *, labels=None) -> Email:
    return Email.from_gmail_message(
        message_id=message_id,
        thread_id="t1",
        subject="Hello",
        from_address="sender@example.com",
        body="Body",
        labels=labels if labels is not None else ["INBOX"],
    )


class TestForwardEmailUseCase:
    def test_allowed_recipient_forwards_and_emits_event(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = ForwardEmailUseCase(gateway, _validator(), repo, bus)

        uc.execute(ForwardEmailCommand(email_id=email.id, to_address="dest@corp.com"))

        assert len(gateway.sent) == 1
        events = [e for e in bus.published if isinstance(e, EmailForwarded)]
        assert len(events) == 1
        assert events[0].email_id == email.id
        assert events[0].forwarded_to == "dest@corp.com"

    def test_blocked_recipient_denied(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        uc = ForwardEmailUseCase(
            gateway,
            _validator(allowed_recipients=["@corp.com"]),
            repo,
            InMemoryEventBus(),
        )
        with pytest.raises(PermissionError):
            uc.execute(ForwardEmailCommand(email_id=email.id, to_address="x@evil.com"))
        assert gateway.sent == []

    def test_rate_limit_exceeded_denied(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        uc = ForwardEmailUseCase(
            gateway, _validator(rate_limits={"forward": 1}), repo, InMemoryEventBus()
        )
        cmd = ForwardEmailCommand(email_id=email.id, to_address="a@b.com")
        uc.execute(cmd)
        with pytest.raises(PermissionError):
            uc.execute(cmd)
        assert len(gateway.sent) == 1

    def test_read_only_denies_forward(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        uc = ForwardEmailUseCase(
            StubGmailGateway(),
            RailguardValidator(RailguardConfig()),  # read_only
            repo,
            InMemoryEventBus(),
        )
        with pytest.raises(PermissionError):
            uc.execute(ForwardEmailCommand(email_id=email.id, to_address="a@b.com"))


class TestArchiveEmailUseCase:
    def test_archive_single_removes_inbox_and_emits(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = ArchiveEmailUseCase(gateway, _validator(), repo, bus)

        uc.execute(ArchiveEmailCommand(email_id=email.id))

        assert gateway.modify_calls == [("m1", [], ["INBOX"])]
        assert any(isinstance(e, EmailArchived) for e in bus.published)

    def test_archive_thread_archives_each_email(self) -> None:
        repo = InMemoryEmailRepository()
        e1, e2 = _email("m1"), _email("m2")
        repo.add(e1)
        repo.add(e2)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = ArchiveEmailUseCase(gateway, _validator(), repo, bus)

        uc.execute(ArchiveEmailCommand(thread_id="t1"))

        assert len(gateway.modify_calls) == 2
        assert sum(isinstance(e, EmailArchived) for e in bus.published) == 2

    def test_blocked_action_denied(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        uc = ArchiveEmailUseCase(
            gateway, _validator(blocked_actions=["archive"]), repo, InMemoryEventBus()
        )
        with pytest.raises(PermissionError):
            uc.execute(ArchiveEmailCommand(email_id=email.id))
        assert gateway.modify_calls == []


class TestDeleteEmailUseCase:
    def test_soft_delete_trashes(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = DeleteEmailUseCase(gateway, _validator(), repo, bus)

        uc.execute(DeleteEmailCommand(email_id=email.id))

        assert gateway.trashed == ["m1"]
        assert gateway.deleted == []
        assert any(isinstance(e, EmailDeleted) for e in bus.published)

    def test_permanent_delete_blocked_action(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email(labels=[])  # archived
        repo.add(email)
        gateway = StubGmailGateway()
        uc = DeleteEmailUseCase(
            gateway,
            _validator(blocked_actions=["permanent_delete"]),
            repo,
            InMemoryEventBus(),
        )
        with pytest.raises(PermissionError):
            uc.execute(DeleteEmailCommand(email_id=email.id, permanent=True))
        assert gateway.deleted == []

    def test_archive_first_blocks_permanent_delete_of_inbox_email(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email(labels=["INBOX"])  # not archived
        repo.add(email)
        gateway = StubGmailGateway()
        uc = DeleteEmailUseCase(
            gateway, _validator(archive_first_policy=True), repo, InMemoryEventBus()
        )
        with pytest.raises(PermissionError):
            uc.execute(DeleteEmailCommand(email_id=email.id, permanent=True))

    def test_permanent_delete_of_archived_email_succeeds(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email(labels=[])  # archived
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = DeleteEmailUseCase(
            gateway, _validator(archive_first_policy=True), repo, bus
        )
        uc.execute(DeleteEmailCommand(email_id=email.id, permanent=True))
        assert gateway.deleted == ["m1"]
        assert any(isinstance(e, EmailDeleted) for e in bus.published)


class TestDraftUseCases:
    def test_create_draft_returns_id_without_sending(self) -> None:
        gateway = StubGmailGateway()
        uc = CreateDraftUseCase(gateway, _validator())
        draft_id = uc.execute(
            CreateDraftCommand(to_address="a@b.com", subject="Hi", body="text")
        )
        assert draft_id == "draft-1"
        assert len(gateway.drafts_created) == 1
        assert gateway.sent == []

    def test_send_draft_sends(self) -> None:
        gateway = StubGmailGateway()
        uc = SendDraftUseCase(gateway, _validator())
        result = uc.execute(SendDraftCommand(draft_id="draft-1"))
        assert gateway.drafts_sent == ["draft-1"]
        assert result.message_id == "sent-1"

    def test_create_draft_denied_under_read_only(self) -> None:
        gateway = StubGmailGateway()
        uc = CreateDraftUseCase(gateway, RailguardValidator(RailguardConfig()))
        with pytest.raises(PermissionError):
            uc.execute(CreateDraftCommand(to_address="a@b.com"))
        assert gateway.drafts_created == []
