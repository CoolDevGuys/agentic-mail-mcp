from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.ValueObjects import GmailMessageId, ThreadId

_VALID_LABEL_TYPES = frozenset({"system", "user", "all"})


@dataclass(frozen=True)
class SearchEmailsQuery:
    query_string: str = ""
    from_address: str | None = None
    to_address: str | None = None
    subject: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    has_attachment: bool = False
    label: str | None = None
    unread_only: bool = False
    page: int = 1
    page_size: int = 25
    page_token: str | None = None

    def __post_init__(self) -> None:
        if self.page < 1:
            raise ValidationError(f"page must be >= 1, got {self.page}")
        if self.page_size < 1:
            raise ValidationError(f"page_size must be >= 1, got {self.page_size}")


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
