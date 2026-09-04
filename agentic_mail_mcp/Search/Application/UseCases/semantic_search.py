from __future__ import annotations

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository
from agentic_mail_mcp.Search.Application.UseCases.dtos import SearchResultDTO
from agentic_mail_mcp.Search.Domain.Gateway.embedding_gateway import EmbeddingGateway
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    VectorSearchRepository,
)


class SemanticSearchUseCase:
    """Vectorize a natural-language query and run a similarity search.

    When an ``email_repository`` is supplied, each result also carries the
    matched email's Gmail message id so callers can fetch it directly; matched
    emails that cannot be resolved (or no repository) leave ``message_id`` None.
    """

    def __init__(
        self,
        embedding: EmbeddingGateway,
        repository: VectorSearchRepository,
        *,
        email_repository: EmailRepository | None = None,
    ) -> None:
        self._embedding = embedding
        self._repository = repository
        self._email_repository = email_repository

    def execute(
        self, query: str, limit: int = 10, min_score: float = 0.0
    ) -> list[SearchResultDTO]:
        query_vector = self._embedding.embed(query)
        results = self._repository.search(query_vector, limit, min_score)
        return [
            SearchResultDTO.from_result(r, message_id=self._message_id(r.email_id))
            for r in results
        ]

    def _message_id(self, email_id: UUIDId) -> str | None:
        if self._email_repository is None:
            return None
        email = self._email_repository.find_by_id(email_id)
        return email.message_id.value if email is not None else None
