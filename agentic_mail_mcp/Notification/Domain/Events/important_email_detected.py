from dataclasses import dataclass, field
from datetime import UTC, datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class ImportantEmailDetected:
    email_id: UUIDId
    from_address: str
    subject: str
    priority: int
    detected_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not 1 <= self.priority <= 5:
            raise ValidationError("priority must be between 1 and 5")
