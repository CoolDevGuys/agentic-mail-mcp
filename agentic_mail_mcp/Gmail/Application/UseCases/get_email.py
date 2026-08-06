from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Application.DTO.dtos import EmailDTO
from agentic_mail_mcp.Gmail.Application.Queries.queries import GetEmailQuery
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository


class GetEmailUseCase:
    """Resolve a single email by UUID (local cache) or GmailMessageId (API).

    A local cache miss for a Gmail message id falls back to the live gateway.
    """

    def __init__(self, gateway: GmailGateway, repository: EmailRepository) -> None:
        self._gateway = gateway
        self._repository = repository

    def execute(self, query: GetEmailQuery) -> EmailDTO:
        identifier = query.email_id
        if isinstance(identifier, UUIDId):
            email = self._repository.find_by_id(identifier)
            if email is None:
                raise NotFoundError(f"Email not found: {identifier}")
            return EmailDTO.from_entity(email)

        message_id = identifier.value
        cached = self._repository.find_by_gmail_message_id(message_id)
        if cached is not None:
            return EmailDTO.from_entity(cached)

        message = self._gateway.get_message(message_id, "full")
        if message is None:
            raise NotFoundError(f"Email not found: {message_id}")
        return EmailDTO.from_gateway_message(message)
