import uuid
from dataclasses import dataclass

from .base import ValueObject


@dataclass(frozen=True)
class UUIDId(ValueObject):
    """Value object wrapping uuid.UUID with generation factory."""

    value: uuid.UUID

    @classmethod
    def generate(cls) -> "UUIDId":
        return cls(value=uuid.uuid4())

    @classmethod
    def from_uuid(cls, uuid_value: uuid.UUID) -> "UUIDId":
        return cls(value=uuid_value)

    @classmethod
    def from_string(cls, uuid_str: str) -> "UUIDId":
        return cls(value=uuid.UUID(uuid_str))

    def __str__(self) -> str:
        return str(self.value)
