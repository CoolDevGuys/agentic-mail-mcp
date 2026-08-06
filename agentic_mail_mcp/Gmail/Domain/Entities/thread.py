from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import NamedTuple

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId

from ..ValueObjects import ThreadId


class _EmailEntry(NamedTuple):
    email_id: UUIDId
    date_sent: datetime


@dataclass
class Thread:
    id: UUIDId
    thread_id: ThreadId
    snippet: str = ""
    subject: str = ""
    participants: list[str] = field(default_factory=list)
    _emails: list[_EmailEntry] = field(default_factory=list)
    last_updated: datetime | None = field(default=None)
    is_read: bool = False

    def __post_init__(self) -> None:
        if self.last_updated is None:
            self.last_updated = datetime.now(UTC)

    @property
    def email_ids(self) -> tuple[UUIDId, ...]:
        return tuple(entry.email_id for entry in self._emails)

    @classmethod
    def create(
        cls,
        thread_id: ThreadId,
        email_ids: list[UUIDId],
        subject: str = "",
        snippet: str = "",
        participants: list[str] | None = None,
    ) -> Thread:
        if not email_ids:
            raise ValidationError("Thread must contain at least one email")
        now = datetime.now(UTC)
        emails = [_EmailEntry(eid, now) for eid in email_ids]
        return cls(
            id=UUIDId.generate(),
            thread_id=thread_id,
            subject=subject,
            snippet=snippet,
            participants=participants or [],
            _emails=emails,
        )

    def add_email(self, email_id: UUIDId, *, date_sent: datetime | None = None) -> None:
        if email_id in self.email_ids:
            return
        sent = date_sent or datetime.now(UTC)
        entry = _EmailEntry(email_id, sent)
        self._emails.append(entry)
        self._emails.sort(key=lambda e: e.date_sent)
        self.last_updated = datetime.now(UTC)

    def mark_read(self) -> None:
        self.is_read = True

    def add_label(self, label: str) -> None:
        pass

    def archive(self) -> None:
        pass

    def move_to_trash(self) -> None:
        pass
