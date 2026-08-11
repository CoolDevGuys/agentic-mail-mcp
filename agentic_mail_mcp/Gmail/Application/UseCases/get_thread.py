from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Gmail.Application.DTO.dtos import ThreadDTO
from agentic_mail_mcp.Gmail.Application.Queries.queries import GetThreadQuery
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway


class GetThreadUseCase:
    """Resolve a conversation thread, with every message's full body, live
    from Gmail (``users.threads.get``) rather than a local mirror — Gmail is
    the only source that has the whole thread already assembled."""

    def __init__(self, gateway: GmailGateway) -> None:
        self._gateway = gateway

    def execute(self, query: GetThreadQuery) -> ThreadDTO:
        thread = self._gateway.get_thread(query.value)
        if thread is None:
            raise NotFoundError(f"Thread not found: {query.value}")
        return ThreadDTO.from_gateway_thread(thread)
