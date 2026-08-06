from dataclasses import dataclass
from datetime import datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class Summary:
    id: UUIDId
    email_id: UUIDId
    summary_text: str
    model_used: str
    created_at: datetime

    def __post_init__(self) -> None:
        if not self.summary_text or not self.summary_text.strip():
            raise ValidationError("summary_text must not be empty")
