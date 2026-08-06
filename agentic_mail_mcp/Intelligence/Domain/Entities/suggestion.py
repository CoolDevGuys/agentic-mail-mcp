from dataclasses import dataclass
from datetime import datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId

_VALID_SUGGESTION_TYPES = {"reply", "forward", "ignore"}


@dataclass
class Suggestion:
    id: UUIDId
    email_id: UUIDId
    suggestion_type: str
    draft_text: str | None
    model_used: str
    created_at: datetime

    def __post_init__(self) -> None:
        if self.suggestion_type not in _VALID_SUGGESTION_TYPES:
            raise ValidationError(
                f"suggestion_type must be one of {sorted(_VALID_SUGGESTION_TYPES)}, got {self.suggestion_type!r}"
            )
