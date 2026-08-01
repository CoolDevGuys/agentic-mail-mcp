from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from src.Common.Domain.ValueObjects.uuid_id import UUIDId

from ..Entities.search_document import SearchDocument


@dataclass
class SearchResult:
    document_id: UUIDId
    email_id: UUIDId
    score: float
    metadata: dict[str, str]


class VectorSearchRepository(Protocol):
    def index(self, document: SearchDocument) -> None: ...

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_score: float = 0.0,
    ) -> list[SearchResult]: ...

    def delete(self, email_id: UUIDId) -> None: ...

    def count(self) -> int: ...
