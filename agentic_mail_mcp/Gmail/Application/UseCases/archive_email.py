from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Common.Railguards.validator import (
    RailguardRequest,
    RailguardValidator,
)
from agentic_mail_mcp.Gmail.Application.Commands.commands import ArchiveEmailCommand
from agentic_mail_mcp.Gmail.Domain.Events import EmailArchived
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository

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
        if command.message_id is not None:
            email = self._email_repository.find_by_gmail_message_id(command.message_id)
            if email is None:
                raise NotFoundError(f"Email not found: {command.message_id}")
            self._archive(email.id, email.message_id.value)
        elif command.thread_id is not None:
            emails = self._email_repository.find_by_thread_id(command.thread_id)
            for email in emails:
                self._archive(email.id, email.message_id.value)

    def _archive(self, email_id: UUIDId, message_id: str) -> None:
        self._gateway.modify_message(message_id, [], [_INBOX])
        self._event_bus.publish(EmailArchived(email_id=email_id))
