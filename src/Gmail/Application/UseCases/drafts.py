from __future__ import annotations

from src.Common.Railguards.validator import RailguardRequest, RailguardValidator
from src.Gmail.Application.Commands.commands import (
    CreateDraftCommand,
    SendDraftCommand,
)
from src.Gmail.Application.UseCases.message_builder import build_draft_message
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway, SentMessageResult


class CreateDraftUseCase:
    """Creates a draft for human review without sending it."""

    def __init__(
        self, gateway: GmailGateway, validator: RailguardValidator
    ) -> None:
        self._gateway = gateway
        self._validator = validator

    def execute(self, command: CreateDraftCommand) -> str:
        self._validator.validate(RailguardRequest(action="create_draft"))
        raw = build_draft_message(command)
        return self._gateway.create_draft(raw).draft_id


class SendDraftUseCase:
    """Sends a previously created, human-reviewed draft."""

    def __init__(
        self, gateway: GmailGateway, validator: RailguardValidator
    ) -> None:
        self._gateway = gateway
        self._validator = validator

    def execute(self, command: SendDraftCommand) -> SentMessageResult:
        self._validator.validate(RailguardRequest(action="send_draft"))
        return self._gateway.send_draft(command.draft_id)
