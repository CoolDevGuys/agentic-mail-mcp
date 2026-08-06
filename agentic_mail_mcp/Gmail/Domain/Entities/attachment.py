from __future__ import annotations

from dataclasses import dataclass

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.base import ValueObject
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass(frozen=True)
class AttachmentMetadata(ValueObject):
    name: str
    mime_type: str
    size_bytes: int

    def __post_init__(self) -> None:
        if not self.name:
            raise ValidationError("Attachment name must not be empty")
        if self.size_bytes < 0:
            raise ValidationError("Attachment size_bytes must be non-negative")


@dataclass
class Attachment:
    id: UUIDId
    file_name: str
    mime_type: str
    size_bytes: int
    attachment_id: str
    download_url: str = ""
