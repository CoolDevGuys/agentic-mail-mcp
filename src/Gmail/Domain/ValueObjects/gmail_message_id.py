from dataclasses import dataclass

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.base import ValueObject


@dataclass(frozen=True)
class GmailMessageId(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValidationError("Gmail message ID must be a non-empty string")
