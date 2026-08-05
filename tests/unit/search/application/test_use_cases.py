from __future__ import annotations

import pytest

from src.Common.Domain.Exceptions import NotFoundError, ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.IdGenerator import UuidIdGenerator
from src.Gmail.Domain.Entities.email import Email
from src.Search.Application.UseCases.dtos import SearchResultDTO
from src.Search.Application.UseCases.index_email import (
    IndexEmailUseCase,
    extract_indexable_text,
)
from src.Search.Application.UseCases.rebuild_index import RebuildIndexUseCase
from src.Search.Application.UseCases.semantic_search import SemanticSearchUseCase
from src.Search.Domain.Repository.vector_search_repository import SearchResult
from tests.fakes.ports import (
    InMemoryEmailRepository,
    InMemoryVectorSearchRepository,
    StubEmbeddingGateway,
)


def _email(message_id: str = "m1") -> Email:
    return Email.from_gmail_message(
        message_id=message_id,
        thread_id="t1",
        subject="Meeting",
        snippet="snip",
        from_address="a@b.com",
        body="Let us meet tomorrow",
    )


class TestSemanticSearchUseCase:
    def test_returns_scored_results_above_threshold(self) -> None:
        repo = InMemoryVectorSearchRepository()
        doc_id, email_id = UUIDId.generate(), UUIDId.generate()
        repo.search_results = [
            SearchResult(
                document_id=doc_id,
                email_id=email_id,
                score=0.9,
                metadata={"subject": "x"},
            ),
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.5,
                metadata={},
            ),
        ]
        uc = SemanticSearchUseCase(StubEmbeddingGateway(), repo)
        results = uc.execute("meeting", limit=10, min_score=0.6)

        assert len(results) == 1
        assert isinstance(results[0], SearchResultDTO)
        assert results[0].document_id == str(doc_id)
        assert results[0].score == 0.9

    def test_honors_limit(self) -> None:
        repo = InMemoryVectorSearchRepository()
        repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.9 - i * 0.01,
                metadata={},
            )
            for i in range(5)
        ]
        uc = SemanticSearchUseCase(StubEmbeddingGateway(), repo)
        assert len(uc.execute("q", limit=2, min_score=0.0)) == 2

    def test_no_matches_returns_empty(self) -> None:
        repo = InMemoryVectorSearchRepository()
        repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.3,
                metadata={},
            )
        ]
        uc = SemanticSearchUseCase(StubEmbeddingGateway(), repo)
        assert uc.execute("q", min_score=0.9) == []


class TestIndexEmailUseCase:
    def test_indexes_email(self) -> None:
        email_repo = InMemoryEmailRepository()
        email = _email()
        email_repo.add(email)
        vector_repo = InMemoryVectorSearchRepository()
        uc = IndexEmailUseCase(
            email_repo,
            StubEmbeddingGateway(dimension=4),
            vector_repo,
            UuidIdGenerator(),
        )
        doc_id = uc.execute(email.id)

        assert vector_repo.count() == 1
        stored = vector_repo.documents[email.id]
        assert stored.id == doc_id
        assert len(stored.embedding) == 4
        assert stored.metadata["subject"] == "Meeting"

    def test_extract_indexable_text(self) -> None:
        text = extract_indexable_text(_email())
        assert "Meeting" in text and "Let us meet tomorrow" in text

    def test_missing_email_raises(self) -> None:
        uc = IndexEmailUseCase(
            InMemoryEmailRepository(),
            StubEmbeddingGateway(),
            InMemoryVectorSearchRepository(),
            UuidIdGenerator(),
        )
        with pytest.raises(NotFoundError):
            uc.execute(UUIDId.generate())

    def test_dimension_mismatch_raises(self) -> None:
        class BadEmbedding(StubEmbeddingGateway):
            def embed(self, text: str) -> list[float]:
                return [0.1, 0.2]  # length 2, but dimension() says 4

        email_repo = InMemoryEmailRepository()
        email = _email()
        email_repo.add(email)
        uc = IndexEmailUseCase(
            email_repo,
            BadEmbedding(dimension=4),
            InMemoryVectorSearchRepository(),
            UuidIdGenerator(),
        )
        with pytest.raises(ValidationError):
            uc.execute(email.id)


class TestRebuildIndexUseCase:
    def test_full_rebuild(self) -> None:
        email_repo = InMemoryEmailRepository()
        ids = []
        for i in range(3):
            email = _email(f"m{i}")
            email_repo.add(email)
            ids.append(email.id)
        vector_repo = InMemoryVectorSearchRepository()
        index_uc = IndexEmailUseCase(
            email_repo, StubEmbeddingGateway(), vector_repo, UuidIdGenerator()
        )
        uc = RebuildIndexUseCase(index_uc)

        stats = uc.execute(ids)
        assert stats.rebuilt == 3
        assert vector_repo.count() == 3

    def test_empty_index(self) -> None:
        email_repo = InMemoryEmailRepository()
        index_uc = IndexEmailUseCase(
            email_repo,
            StubEmbeddingGateway(),
            InMemoryVectorSearchRepository(),
            UuidIdGenerator(),
        )
        uc = RebuildIndexUseCase(index_uc)
        assert uc.execute([]).rebuilt == 0
