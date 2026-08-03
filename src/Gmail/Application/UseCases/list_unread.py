from __future__ import annotations

from src.Gmail.Application.DTO.dtos import EmailDTO
from src.Gmail.Application.Queries.queries import ListUnreadQuery
from src.Gmail.Domain.Repository.email_repository import EmailRepository


class ListUnreadUseCase:
    """Return unread emails as DTOs, optionally filtered by label."""

    def __init__(self, repository: EmailRepository) -> None:
        self._repository = repository

    def execute(self, query: ListUnreadQuery) -> list[EmailDTO]:
        emails = self._repository.list_unread(query.limit)
        if query.label is not None:
            emails = [e for e in emails if query.label in e.labels]
        return [EmailDTO.from_entity(e) for e in emails]
