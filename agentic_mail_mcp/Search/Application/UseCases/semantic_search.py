from __future__ import annotations

from agentic_mail_mcp.Search.Application.UseCases.dtos import SearchResultDTO
from agentic_mail_mcp.Search.Domain.Gateway.embedding_gateway import EmbeddingGateway
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    VectorSearchRepository,
)


class SemanticSearchUseCase:
    """Vectorize a natural-language query and run a similarity search."""

    def __init__(
        self,
        embedding: EmbeddingGateway,
        repository: VectorSearchRepository,
    ) -> None:
        self._embedding = embedding
        self._repository = repository

    def execute(
        self, query: str, limit: int = 10, min_score: float = 0.0
    ) -> list[SearchResultDTO]:
        query_vector = self._embedding.embed(query)
        results = self._repository.search(query_vector, limit, min_score)
        return [SearchResultDTO.from_result(r) for r in results]
