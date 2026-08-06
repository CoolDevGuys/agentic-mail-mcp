from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Common.Domain.Exceptions import NotFoundError
from src.Common.Railguards.validator import RailguardRequest, RailguardValidator
from src.Gmail.Application.Commands.commands import DeleteEmailCommand
from src.Gmail.Domain.Events import EmailDeleted
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from src.Gmail.Domain.Repository.email_repository import EmailRepository

_INBOX = "INBOX"


class DeleteEmailUseCase:
    """Trashes an email by default; permanently deletes only when the railguards
    allow it (action not blocked, archive-first satisfied)."""

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

    def execute(self, command: DeleteEmailCommand) -> None:
        email = self._email_repository.find_by_gmail_message_id(command.message_id)
        if email is None:
            raise NotFoundError(f"Email not found: {command.message_id}")

        # Labels come from the read-through repository, which resolves the email
        # live from Gmail, so the archive-first gate sees the current state.
        is_archived = _INBOX not in email.labels
        action = "permanent_delete" if command.permanent else "delete"
        self._validator.validate(
            RailguardRequest(action=action, is_archived=is_archived)
        )

        if command.permanent:
            self._gateway.delete_message(email.message_id.value)
        else:
            self._gateway.trash_message(email.message_id.value)
        self._event_bus.publish(EmailDeleted(email_id=email.id))
