from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Common.Railguards.validator import (
    RailguardRequest,
    RailguardValidator,
)
from agentic_mail_mcp.Gmail.Application.Commands.commands import AddLabelCommand
from agentic_mail_mcp.Gmail.Domain.Events import EmailLabeled
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository


class AddLabelUseCase:
    """Adds a label to an email after railguard validation.

    Follows the Phase-6 railguarded write pattern: validate -> gateway ->
    publish. The ``EmailLabeled`` event is emitted only after the gateway call
    succeeds, so a failed modification never records a label that was not set.
    """

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

    def execute(self, command: AddLabelCommand) -> None:
        self._validator.validate(RailguardRequest(action="add_label"))
        email = self._email_repository.find_by_gmail_message_id(command.message_id)
        if email is None:
            raise NotFoundError(f"Email not found: {command.message_id}")

        self._gateway.modify_message(email.message_id.value, [command.label_name], [])
        self._event_bus.publish(
            EmailLabeled(email_id=email.id, label_name=command.label_name)
        )
