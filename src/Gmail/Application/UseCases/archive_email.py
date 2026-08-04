from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Common.Domain.Exceptions import NotFoundError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Railguards.validator import RailguardRequest, RailguardValidator
from src.Gmail.Application.Commands.commands import ArchiveEmailCommand
from src.Gmail.Domain.Events import EmailArchived
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from src.Gmail.Domain.Repository.email_repository import EmailRepository

_INBOX = "INBOX"


class ArchiveEmailUseCase:
    """Archives an email or thread (removes the INBOX label) after validation."""

    def __init__(
        self,
        gateway: GmailGateway,
        validator: RailguardValidator,
        email_repository: EmailRepository,
        event_bus: EventBus,
    ) -> None:
        self._gateway = gateway
        self._validator = validator
        self._email_repository = email_repository
        self._event_bus = event_bus

    def execute(self, command: ArchiveEmailCommand) -> None:
        self._validator.validate(RailguardRequest(action="archive"))
        if command.email_id is not None:
            email = self._email_repository.find_by_id(command.email_id)
            if email is None:
                raise NotFoundError(f"Email not found: {command.email_id}")
            self._archive(email.id, email.message_id.value)
        elif command.thread_id is not None:
            emails = self._email_repository.find_by_thread_id(command.thread_id)
            for email in emails:
                self._archive(email.id, email.message_id.value)

    def _archive(self, email_id: UUIDId, message_id: str) -> None:
        self._gateway.modify_message(message_id, [], [_INBOX])
        self._event_bus.publish(EmailArchived(email_id=email_id))
