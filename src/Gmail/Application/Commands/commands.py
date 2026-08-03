from __future__ import annotations

from dataclasses import dataclass, field

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId

# Note: execution handlers for the write-oriented commands live in Phase 6
# (railguards framework). Phase 4 defines the command data objects only.


@dataclass(frozen=True)
class ForwardEmailCommand:
    email_id: UUIDId
    to_address: str
    subject: str = ""
    body: str = ""
    include_original: bool = True

    def __post_init__(self) -> None:
        if not self.to_address:
            raise ValidationError("to_address must not be empty")


@dataclass(frozen=True)
class ArchiveEmailCommand:
    email_id: UUIDId | None = None
    thread_id: str | None = None

    def __post_init__(self) -> None:
        if self.email_id is None and self.thread_id is None:
            raise ValidationError("either email_id or thread_id must be provided")


@dataclass(frozen=True)
class DeleteEmailCommand:
    email_id: UUIDId
    permanent: bool = False


@dataclass(frozen=True)
class CreateDraftCommand:
    to_address: str
    subject: str = ""
    body: str = ""
    attachments: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.to_address:
            raise ValidationError("to_address must not be empty")


@dataclass(frozen=True)
class SendDraftCommand:
    draft_id: str

    def __post_init__(self) -> None:
        if not self.draft_id:
            raise ValidationError("draft_id must not be empty")


@dataclass(frozen=True)
class AddLabelCommand:
    email_id: UUIDId
    label_name: str

    def __post_init__(self) -> None:
        if self.email_id is None:
            raise ValidationError("email_id must be provided")
        if not self.label_name:
            raise ValidationError("label_name must not be empty")


@dataclass(frozen=True)
class MarkReadCommand:
    email_id: UUIDId

    def __post_init__(self) -> None:
        if self.email_id is None:
            raise ValidationError("email_id must be provided")
