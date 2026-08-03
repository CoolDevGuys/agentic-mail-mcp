from __future__ import annotations

from src.Common.Domain.Exceptions import NotFoundError, ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.IdGenerator import IdGenerator
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Search.Domain.Entities.search_document import SearchDocument
from src.Search.Domain.Gateway.embedding_gateway import EmbeddingGateway
from src.Search.Domain.Repository.vector_search_repository import VectorSearchRepository


def extract_indexable_text(email: Email) -> str:
    parts = [email.subject, email.snippet, email.body]
    return "\n".join(p for p in parts if p)


class IndexEmailUseCase:
    """Embed an email's text and persist it as a SearchDocument."""

    def __init__(
        self,
        email_repository: EmailRepository,
        embedding: EmbeddingGateway,
        repository: VectorSearchRepository,
        id_generator: IdGenerator,
    ) -> None:
        self._email_repository = email_repository
        self._embedding = embedding
        self._repository = repository
        self._id_generator = id_generator

    def execute(self, email_id: UUIDId) -> UUIDId:
        email = self._email_repository.find_by_id(email_id)
        if email is None:
            raise NotFoundError(f"Email not found: {email_id}")

        content = extract_indexable_text(email)
        vector = self._embedding.embed(content)
        dimension = self._embedding.dimension()
        if len(vector) != dimension:
            raise ValidationError(
                f"Embedding dimension {len(vector)} does not match gateway "
                f"dimension {dimension}"
            )

        document = SearchDocument.create(
            id=self._id_generator.generate(),
            email_id=email.id,
            content=content,
            embedding=vector,
            metadata={
                "subject": email.subject,
                "from": email.from_address.value if email.from_address else "",
            },
            expected_dimension=dimension,
        )
        self._repository.index(document)
        return document.id
