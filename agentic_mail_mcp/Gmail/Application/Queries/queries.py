from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId, ThreadId

_VALID_LABEL_TYPES = frozenset({"system", "user", "all"})
_VALID_DIRECTIONS = frozenset({"received", "sent"})
_VALID_QUERY_SCOPES = frozenset({"all", "subject", "body"})


@dataclass(frozen=True)
class SearchEmailsQuery:
    query_string: str = ""
    # Where the free-text term matches: everywhere (Gmail full-text), the
    # subject only, or the body only.
    query_scope: str = "all"
    from_address: str | None = None
    to_address: str | None = None
    subject: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    has_attachment: bool = False
    label: str | None = None
    unread_only: bool = False
    direction: str | None = None
    include_body: bool = False
    body_max_length: int | None = None
    seen_ids: frozenset[str] = field(default_factory=frozenset)
    page: int = 1
    page_size: int = 25

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValidationError(f"page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValidationError(f"page_size must be >= 1, got {self.page_size}")
        if self.direction is not None and self.direction not in _VALID_DIRECTIONS:
            raise ValidationError(
                f"direction must be one of {sorted(_VALID_DIRECTIONS)}, "
                f"got {self.direction!r}"
            )
        if self.query_scope not in _VALID_QUERY_SCOPES:
            raise ValidationError(
                f"query_scope must be one of {sorted(_VALID_QUERY_SCOPES)}, "
                f"got {self.query_scope!r}"
            )
        if self.body_max_length is not None and self.body_max_length < 1:
            raise ValidationError(
                f"body_max_length must be >= 1, got {self.body_max_length}"
            )


@dataclass(frozen=True)
class GetEmailQuery:
    email_id: UUIDId | GmailMessageId

    def __post_init__(self) -> None:
        if not isinstance(self.email_id, (UUIDId, GmailMessageId)):
            raise ValidationError("email_id must be a UUIDId or GmailMessageId")

    @property
    def is_uuid(self) -> bool:
        return isinstance(self.email_id, UUIDId)


@dataclass(frozen=True)
class GetThreadQuery:
    thread_id: str | ThreadId

    def __post_init__(self) -> None:
        if not self.value:
            raise ValidationError("thread_id must not be empty")

    @property
    def value(self) -> str:
        if isinstance(self.thread_id, ThreadId):
            return self.thread_id.value
        return self.thread_id


@dataclass(frozen=True)
class ListUnreadQuery:
    limit: int = 25
    label: str | None = None

    def __post_init__(self) -> None:
        if self.limit < 1:
            raise ValidationError(f"limit must be >= 1, got {self.limit}")


@dataclass(frozen=True)
class ListLabelsQuery:
    label_type: str = "all"

    def __post_init__(self) -> None:
        if self.label_type not in _VALID_LABEL_TYPES:
            raise ValidationError(
                f"label_type must be one of {sorted(_VALID_LABEL_TYPES)}, "
                f"got {self.label_type!r}"
            )
