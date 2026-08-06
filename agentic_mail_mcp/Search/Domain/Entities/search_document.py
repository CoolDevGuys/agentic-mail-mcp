from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class SearchDocument:
    id: UUIDId
    email_id: UUIDId
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
    _expected_dimension: int | None = None

    def __post_init__(self) -> None:
        if (
            self._expected_dimension is not None
            and len(self.embedding) != self._expected_dimension
        ):
            raise ValidationError(
                f"embedding dimension {len(self.embedding)} does not match "
                f"expected dimension {self._expected_dimension}"
            )

    @classmethod
    def create(
        cls,
        *,
        id: UUIDId,
        email_id: UUIDId,
        content: str,
        embedding: list[float] | None = None,
        metadata: dict[str, str] | None = None,
        expected_dimension: int | None = None,
    ) -> SearchDocument:
        return cls(
            id=id,
            email_id=email_id,
            content=content,
            embedding=embedding or [],
            metadata=metadata or {},
            _expected_dimension=expected_dimension,
        )
