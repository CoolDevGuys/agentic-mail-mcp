from __future__ import annotations

from dataclasses import dataclass

from src.Search.Domain.Repository.vector_search_repository import SearchResult


@dataclass(frozen=True)
class SearchResultDTO:
    document_id: str
    email_id: str
    score: float
    metadata: dict[str, str]

    @classmethod
    def from_result(cls, result: SearchResult) -> SearchResultDTO:
        return cls(
            document_id=str(result.document_id),
            email_id=str(result.email_id),
            score=result.score,
            metadata=dict(result.metadata),
        )


@dataclass(frozen=True)
class RebuildStats:
    rebuilt: int
