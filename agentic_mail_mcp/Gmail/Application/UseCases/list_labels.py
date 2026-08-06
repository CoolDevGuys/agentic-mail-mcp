from __future__ import annotations

from agentic_mail_mcp.Gmail.Application.DTO.dtos import LabelDTO
from agentic_mail_mcp.Gmail.Application.Queries.queries import ListLabelsQuery
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway


class ListLabelsUseCase:
    """Return labels as DTOs filtered by type (system, user, or all)."""

    def __init__(self, gateway: GmailGateway) -> None:
        self._gateway = gateway

    def execute(self, query: ListLabelsQuery) -> list[LabelDTO]:
        labels = self._gateway.list_labels()
        if query.label_type != "all":
            labels = [label for label in labels if label.type == query.label_type]
        return [LabelDTO.from_gateway_label(label) for label in labels]
