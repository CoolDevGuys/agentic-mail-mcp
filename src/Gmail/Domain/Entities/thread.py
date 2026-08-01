from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId

from ..ValueObjects import ThreadId


@dataclass
class Thread:
    id: UUIDId
    thread_id: ThreadId
    snippet: str = ""
    subject: str = ""
    participants: list[str] = field(default_factory=list)
    _email_ids: list[UUIDId] = field(default_factory=list)
    last_updated: datetime | None = field(default=None)
    is_read: bool = False

    def __post_init__(self) -> None:
        if self.last_updated is None:
            self.last_updated = datetime.now(UTC)

    @property
    def email_ids(self) -> tuple[UUIDId, ...]:
        return tuple(self._email_ids)

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
        return cls(
            id=UUIDId.generate(),
            thread_id=thread_id,
            subject=subject,
            snippet=snippet,
            participants=participants or [],
            _email_ids=list(email_ids),
        )

    def add_email(self, email_id: UUIDId) -> None:
        if email_id not in self._email_ids:
            self._email_ids.append(email_id)
            self.last_updated = datetime.now(UTC)

    def mark_read(self) -> None:
        self.is_read = True

    def add_label(self, label: str) -> None:
        pass

    def archive(self) -> None:
        pass

    def move_to_trash(self) -> None:
        pass
