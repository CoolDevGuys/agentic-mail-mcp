from __future__ import annotations

from dataclasses import dataclass, field

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError

# Write commands identify the target email by its Gmail ``message_id`` (the
# tool-facing id). The use cases resolve it to the domain email via the
# read-through repository; the internal UUID stays an implementation detail.


@dataclass(frozen=True)
class ForwardEmailCommand:
    message_id: str
    to_address: str
    subject: str = ""
    body: str = ""
    include_original: bool = True

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValidationError("message_id must not be empty")
        if not self.to_address:
            raise ValidationError("to_address must not be empty")


@dataclass(frozen=True)
class ArchiveEmailCommand:
    message_id: str | None = None
    thread_id: str | None = None

    def __post_init__(self) -> None:
        if not self.message_id and self.thread_id is None:
            raise ValidationError("either message_id or thread_id must be provided")


@dataclass(frozen=True)
class DeleteEmailCommand:
    message_id: str
    permanent: bool = False

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValidationError("message_id must not be empty")


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
    message_id: str
    label_name: str

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValidationError("message_id must be provided")
        if not self.label_name:
            raise ValidationError("label_name must not be empty")


@dataclass(frozen=True)
class MarkReadCommand:
    message_id: str

    def __post_init__(self) -> None:
        if not self.message_id:
            raise ValidationError("message_id must be provided")
