from __future__ import annotations

from datetime import UTC, datetime

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Search.Domain.Entities.search_document import SearchDocument


class TestSearchDocumentCreation:
    def test_create_with_required_fields(self) -> None:
        doc = SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content="test content",
        )

        assert isinstance(doc.id, UUIDId)
        assert isinstance(doc.email_id, UUIDId)
        assert doc.content == "test content"
        assert doc.embedding == []
        assert doc.metadata == {}
        assert isinstance(doc.created_at, datetime)

    def test_create_with_all_fields(self) -> None:
        doc_id = UUIDId.generate()
        email_id = UUIDId.generate()
        now = datetime.now(tz=UTC)

        doc = SearchDocument(
            id=doc_id,
            email_id=email_id,
            content="hello world",
            embedding=[0.1, 0.2, 0.3],
            metadata={"subject": "Test", "sender": "test@example.com"},
            created_at=now,
        )

        assert doc.id == doc_id
        assert doc.email_id == email_id
        assert doc.content == "hello world"
        assert doc.embedding == [0.1, 0.2, 0.3]
        assert doc.metadata == {"subject": "Test", "sender": "test@example.com"}
        assert doc.created_at == now

    def test_embedding_defaults_to_empty_list(self) -> None:
        doc = SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content="content",
        )

        assert doc.embedding == []
        assert isinstance(doc.embedding, list)

    def test_metadata_defaults_to_empty_dict(self) -> None:
        doc = SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content="content",
        )

        assert doc.metadata == {}
        assert isinstance(doc.metadata, dict)

    def test_mutating_defaults_does_not_affect_other_instances(self) -> None:
        doc1 = SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content="doc1",
        )
        doc1.embedding.append(0.5)
        doc1.metadata["key"] = "value"

        doc2 = SearchDocument(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            content="doc2",
        )

        assert doc2.embedding == []
        assert doc2.metadata == {}
