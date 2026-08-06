"""Backend-agnostic contract for VectorSearchRepository implementations.

Subclasses provide a ``vector_repo`` fixture bound to a concrete backend
(sqlite-vec, pgvector, ...). Identical behavior across backends guarantees
interchangeability.
"""

from __future__ import annotations

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Search.Domain.Entities.search_document import SearchDocument


def _doc(email_seed: str, embedding: list[float]) -> SearchDocument:
    return SearchDocument.create(
        id=UUIDId.generate(),
        email_id=UUIDId.generate(),
        content=f"content {email_seed}",
        embedding=embedding,
        metadata={"subject": email_seed},
    )


class VectorSearchRepositoryContractTests:
    dimension = 4

    def test_index_then_search_returns_document(self, vector_repo) -> None:
        target = _doc("a", [1.0, 0.0, 0.0, 0.0])
        other = _doc("b", [0.0, 1.0, 0.0, 0.0])
        vector_repo.index(target)
        vector_repo.index(other)

        results = vector_repo.search([1.0, 0.0, 0.0, 0.0], limit=1, min_score=0.0)
        assert results
        assert results[0].email_id == target.email_id
        assert results[0].metadata["subject"] == "a"

    def test_count_reflects_indexed_documents(self, vector_repo) -> None:
        vector_repo.index(_doc("a", [1.0, 0.0, 0.0, 0.0]))
        vector_repo.index(_doc("b", [0.0, 1.0, 0.0, 0.0]))
        assert vector_repo.count() == 2

    def test_delete_removes_document(self, vector_repo) -> None:
        doc = _doc("a", [1.0, 0.0, 0.0, 0.0])
        vector_repo.index(doc)
        vector_repo.delete(doc.email_id)
        assert vector_repo.count() == 0
        assert vector_repo.search([1.0, 0.0, 0.0, 0.0], limit=5) == []

    def test_limit_caps_results(self, vector_repo) -> None:
        for i in range(4):
            vec = [0.0, 0.0, 0.0, 0.0]
            vec[i % 4] = 1.0
            vector_repo.index(_doc(str(i), vec))
        assert len(vector_repo.search([1.0, 0.0, 0.0, 0.0], limit=2)) <= 2
