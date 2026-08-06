from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from agentic_mail_mcp.Common.Domain.Exceptions import DomainError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Events import (
    EmailArchived,
    EmailDeleted,
    EmailLabeled,
    EmailRead,
)
from agentic_mail_mcp.Gmail.Domain.ValueObjects import (
    EmailAddress,
    GmailMessageId,
    ThreadId,
)


@dataclass
class Email:
    id: UUIDId
    message_id: GmailMessageId
    thread_id: ThreadId
    snippet: str = ""
    subject: str = ""
    from_address: EmailAddress | None = None
    to_addresses: list[EmailAddress] = field(default_factory=list)
    date_sent: datetime | None = None
    is_read: bool = False
    _labels: set[str] = field(default_factory=set)
    body: str = ""
    _attachments: list[str] = field(default_factory=list)
    _is_trashed: bool = False
    _domain_events: list[object] = field(default_factory=list)

    @property
    def labels(self) -> frozenset[str]:
        return frozenset(self._labels)

    @property
    def is_trashed(self) -> bool:
        return self._is_trashed

    @property
    def attachments(self) -> list[str]:
        return list(self._attachments)

    @property
    def domain_events(self) -> list[object]:
        events = list(self._domain_events)
        self._domain_events.clear()
        return events

    @classmethod
    def from_gmail_message(
        cls,
        message_id: str,
        thread_id: str,
        *,
        snippet: str = "",
        subject: str = "",
        from_address: str | None = None,
        to_addresses: list[str] | None = None,
        date_sent: datetime | None = None,
        body: str = "",
        labels: list[str] | None = None,
    ) -> Email:
        return cls(
            id=UUIDId.generate(),
            message_id=GmailMessageId(message_id),
            thread_id=ThreadId(thread_id),
            snippet=snippet,
            subject=subject,
            from_address=EmailAddress(from_address) if from_address else None,
            to_addresses=[EmailAddress(a) for a in (to_addresses or [])],
            date_sent=date_sent,
            body=body,
            _labels=set(labels or []),
        )

    def mark_read(self) -> None:
        if not self.is_read:
            self.is_read = True
            self._domain_events.append(EmailRead(email_id=self.id))

    def add_label(self, label: str) -> None:
        if label not in self._labels:
            self._labels.add(label)
            self._domain_events.append(EmailLabeled(email_id=self.id, label_name=label))

    def remove_label(self, label: str) -> None:
        self._labels.discard(label)

    def archive(self) -> None:
        self._domain_events.append(EmailArchived(email_id=self.id))

    def move_to_trash(self) -> None:
        self._is_trashed = True
        self._domain_events.append(EmailDeleted(email_id=self.id))

    def restore_from_trash(self) -> None:
        if not self._is_trashed:
            raise DomainError("Cannot restore: email is not in trash")
        self._is_trashed = False
