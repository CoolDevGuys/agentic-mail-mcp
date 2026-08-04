from __future__ import annotations

import pytest

from src.Common.Domain.Events import InMemoryEventBus
from src.Common.Domain.Exceptions import NotFoundError, PermissionError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Railguards.config import RailguardConfig
from src.Common.Railguards.validator import RailguardValidator
from src.Gmail.Application.Commands.commands import AddLabelCommand
from src.Gmail.Application.UseCases.add_label import AddLabelUseCase
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Events import EmailLabeled
from tests.fakes.ports import InMemoryEmailRepository, StubGmailGateway


def _email() -> Email:
    return Email.from_gmail_message(
        message_id="m1", thread_id="t1", subject="Hi", body="Body", labels=["INBOX"]
    )


def _validator(access_level: str = "read_write") -> RailguardValidator:
    return RailguardValidator(RailguardConfig(access_level=access_level))


class TestAddLabelUseCase:
    def test_adds_label_and_emits_event_when_permitted(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = AddLabelUseCase(gateway, _validator(), repo, bus)

        uc.execute(AddLabelCommand(email_id=email.id, label_name="Important"))

        assert gateway.modify_calls == [("m1", ["Important"], [])]
        events = [e for e in bus.published if isinstance(e, EmailLabeled)]
        assert len(events) == 1
        assert events[0].email_id == email.id
        assert events[0].label_name == "Important"

    def test_denied_when_read_only(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = AddLabelUseCase(gateway, _validator("read_only"), repo, bus)

        with pytest.raises(PermissionError):
            uc.execute(AddLabelCommand(email_id=email.id, label_name="Important"))

        assert gateway.modify_calls == []
        assert bus.published == []

    def test_missing_email_raises_not_found(self) -> None:
        repo = InMemoryEmailRepository()
        gateway = StubGmailGateway()
        bus = InMemoryEventBus()
        uc = AddLabelUseCase(gateway, _validator(), repo, bus)

        with pytest.raises(NotFoundError):
            uc.execute(AddLabelCommand(email_id=UUIDId.generate(), label_name="X"))

    def test_no_event_when_gateway_fails(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        bus = InMemoryEventBus()

        class FailingGateway(StubGmailGateway):
            def modify_message(self, *args, **kwargs):
                raise RuntimeError("gateway down")

        uc = AddLabelUseCase(FailingGateway(), _validator(), repo, bus)

        with pytest.raises(RuntimeError):
            uc.execute(AddLabelCommand(email_id=email.id, label_name="X"))

        assert bus.published == []
