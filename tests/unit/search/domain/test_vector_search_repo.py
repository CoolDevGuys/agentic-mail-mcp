from __future__ import annotations

from dataclasses import dataclass, field

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Search.Domain.Entities.search_document import SearchDocument
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)


@dataclass
class _FakeVectorSearchRepository:
    """Minimal fake that satisfies the VectorSearchRepository Protocol."""

    _store: list[SearchDocument] = field(default_factory=list)

    def index(self, document: SearchDocument) -> None:
        self._store.append(document)

    def search(
        self,
        query_vector: list[float],
        limit: int = 10,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for doc in self._store:
            score = _cosine_similarity(query_vector, doc.embedding)
            if score >= min_score:
                results.append(
                    SearchResult(
                        document_id=doc.id,
                        email_id=doc.email_id,
                        score=score,
                        metadata=dict(doc.metadata),
                    )
                )
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def delete(self, email_id: UUIDId) -> None:
        self._store = [d for d in self._store if d.email_id != email_id]

    def count(self) -> int:
        return len(self._store)


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    denominator = norm_a * norm_b
    if denominator == 0:
        return 0.0
    return dot / denominator


class TestVectorSearchRepositoryProtocol:
    def _make_repo(self) -> _FakeVectorSearchRepository:
        return _FakeVectorSearchRepository()

    def _make_doc(
        self,
        *,
        content: str = "test",
        embedding: list[float] | None = None,
        metadata: dict[str, str] | None = None,
    ) -> SearchDocument:
        return SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content=content,
            embedding=embedding or [0.1, 0.2],
            metadata=metadata or {},
        )

    def test_index_adds_document(self) -> None:
        repo = self._make_repo()
        doc = self._make_doc()

        repo.index(doc)

        assert repo.count() == 1

    def test_index_adds_multiple_documents(self) -> None:
        repo = self._make_repo()
        for _ in range(3):
            repo.index(self._make_doc())

        assert repo.count() == 3

    def test_search_returns_results(self) -> None:
        repo = self._make_repo()
        doc = self._make_doc(embedding=[1.0, 0.0])
        repo.index(doc)

        results = repo.search([1.0, 0.0])

        assert len(results) == 1
        assert results[0].document_id == doc.id
        assert results[0].email_id == doc.email_id

    def test_search_respects_limit(self) -> None:
        repo = self._make_repo()
        for _ in range(5):
            repo.index(self._make_doc(embedding=[1.0, 0.0]))

        results = repo.search([1.0, 0.0], limit=2)

        assert len(results) == 2

    def test_search_respects_min_score(self) -> None:
        repo = self._make_repo()
        repo.index(self._make_doc(embedding=[1.0, 0.0]))
        repo.index(self._make_doc(embedding=[0.0, 1.0]))

        results = repo.search([1.0, 0.0], min_score=0.9)

        assert len(results) == 1

    def test_search_returns_empty_when_no_documents(self) -> None:
        repo = self._make_repo()

        results = repo.search([0.1, 0.2])

        assert results == []

    def test_delete_removes_by_email_id(self) -> None:
        repo = self._make_repo()
        doc = self._make_doc()
        repo.index(doc)

        repo.delete(doc.email_id)

        assert repo.count() == 0

    def test_delete_nonexistent_email_id_is_noop(self) -> None:
        repo = self._make_repo()
        doc = self._make_doc()
        repo.index(doc)

        repo.delete(UUIDId.generate())

        assert repo.count() == 1

    def test_search_result_has_metadata(self) -> None:
        repo = self._make_repo()
        doc = self._make_doc(
            embedding=[1.0, 0.0],
            metadata={"subject": "Meeting", "sender": "boss@co.com"},
        )
        repo.index(doc)

        results = repo.search([1.0, 0.0])

        assert results[0].metadata["subject"] == "Meeting"
        assert results[0].metadata["sender"] == "boss@co.com"


class TestSearchResult:
    def test_create_search_result(self) -> None:
        doc_id = UUIDId.generate()
        email_id = UUIDId.generate()

        result = SearchResult(
            document_id=doc_id,
            email_id=email_id,
            score=0.95,
            metadata={"subject": "Test"},
        )

        assert result.document_id == doc_id
        assert result.email_id == email_id
        assert result.score == 0.95
        assert result.metadata == {"subject": "Test"}

    def test_search_result_is_dataclass(self) -> None:
        result = SearchResult(
            document_id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            score=0.5,
            metadata={},
        )

        assert isinstance(result, SearchResult)
