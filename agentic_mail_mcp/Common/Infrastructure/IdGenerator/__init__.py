import uuid
from typing import Protocol

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


class IdGenerator(Protocol):
    """Protocol for generating domain IDs."""

    def generate(self) -> UUIDId: ...


class UuidIdGenerator:
    """Generates UUIDId instances using uuid4."""

    def generate(self) -> UUIDId:
        return UUIDId(value=uuid.uuid4())
