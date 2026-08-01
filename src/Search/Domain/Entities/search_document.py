from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class SearchDocument:
    id: UUIDId
    email_id: UUIDId
    content: str
    embedding: list[float] = field(default_factory=list)
    metadata: dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(tz=UTC))
