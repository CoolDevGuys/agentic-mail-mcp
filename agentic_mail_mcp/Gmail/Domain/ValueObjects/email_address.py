import re
from dataclasses import dataclass

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.base import ValueObject

_EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9]"
    r"(?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?"
    r"(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)*$"
)


@dataclass(frozen=True)
class EmailAddress(ValueObject):
    value: str

    def __post_init__(self) -> None:
        if not self.value or not isinstance(self.value, str):
            raise ValidationError("Email address must be a non-empty string")

        if len(self.value) > 254:
            raise ValidationError(
                f"Email address must not exceed 254 characters, got {len(self.value)}"
            )

        if _EMAIL_REGEX.match(self.value) is None:
            raise ValidationError(f"Invalid email address format: {self.value}")

    @property
    def local_part(self) -> str:
        return self.value.split("@", 1)[0]

    @property
    def domain(self) -> str:
        return self.value.split("@", 1)[1]
