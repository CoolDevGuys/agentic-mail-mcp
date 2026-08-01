from dataclasses import dataclass
from datetime import datetime

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId

_VALID_CATEGORIES = {"urgent", "normal", "spam", "promo"}


@dataclass
class Classification:
    id: UUIDId
    email_id: UUIDId
    category: str
    priority: int
    confidence: float
    model_used: str
    created_at: datetime

    def __post_init__(self) -> None:
        if self.category not in _VALID_CATEGORIES:
            raise ValidationError(
                f"category must be one of {sorted(_VALID_CATEGORIES)}, got {self.category!r}"
            )
        if not 1 <= self.priority <= 5:
            raise ValidationError(f"priority must be between 1 and 5, got {self.priority}")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValidationError(
                f"confidence must be between 0.0 and 1.0, got {self.confidence}"
            )
