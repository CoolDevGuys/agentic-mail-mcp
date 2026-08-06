from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Common.Domain.Exceptions import NotFoundError
from src.Common.Railguards.validator import RailguardRequest, RailguardValidator
from src.Gmail.Application.Commands.commands import ForwardEmailCommand
from src.Gmail.Application.UseCases.message_builder import build_forward_message
from src.Gmail.Domain.Events import EmailForwarded
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway, SentMessageResult
from src.Gmail.Domain.Repository.email_repository import EmailRepository


class ForwardEmailUseCase:
    """Forwards an email after railguard validation (allowlist + rate limit)."""

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

    def execute(self, command: ForwardEmailCommand) -> SentMessageResult:
        self._validator.validate(
            RailguardRequest(action="forward", recipient=command.to_address)
        )
        original = self._email_repository.find_by_gmail_message_id(command.message_id)
        if original is None:
            raise NotFoundError(f"Email not found: {command.message_id}")

        raw = build_forward_message(original, command)
        result = self._gateway.send_message(raw)
        self._event_bus.publish(
            EmailForwarded(email_id=original.id, forwarded_to=command.to_address)
        )
        return result
