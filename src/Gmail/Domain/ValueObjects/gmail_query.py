from dataclasses import dataclass
from datetime import date

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.base import ValueObject


@dataclass(frozen=True)
class GmailQuery(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValidationError("Gmail query must be a non-empty string")

        if len(self.value) > 500:
            raise ValidationError(
                f"Gmail query must not exceed 500 characters, got {len(self.value)}"
            )

    @classmethod
    def from_sender(cls, sender: str) -> "GmailQuery":
        return cls(value=f"from:{sender}")

    @classmethod
    def with_subject(cls, subject: str) -> "GmailQuery":
        return cls(value=f"subject:{subject}")

    @classmethod
    def date_range(
        cls, after: date | None = None, before: date | None = None
    ) -> "GmailQuery":
        parts: list[str] = []
        if after:
            parts.append(f"after:{after.isoformat()}")
        if before:
            parts.append(f"before:{before.isoformat()}")
        if not parts:
            raise ValidationError(
                "At least one of 'after' or 'before' must be provided"
            )
        return cls(value=" ".join(parts))

    @classmethod
    def has_attachment(cls) -> "GmailQuery":
        return cls(value="has:attachment")

    @classmethod
    def with_label(cls, label: str) -> "GmailQuery":
        return cls(value=label)

    @classmethod
    def unread(cls) -> "GmailQuery":
        return cls(value="is:unread")

    def and_(self, other: "GmailQuery") -> "GmailQuery":
        return GmailQuery(value=f"{self.value} {other.value}")
