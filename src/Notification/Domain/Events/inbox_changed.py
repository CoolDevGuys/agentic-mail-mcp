from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class InboxChanged:
    event_type: str
    email_id: UUIDId
    changed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
