from __future__ import annotations

import email.utils
from dataclasses import dataclass, field
from datetime import datetime

from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Entities.label import SYSTEM_LABELS, Label
from agentic_mail_mcp.Gmail.Domain.Entities.thread import Thread
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailLabel,
    GmailMessage,
    GmailMessageHeader,
)


@dataclass(frozen=True)
class EmailDTO:
    id: str
    message_id: str
    thread_id: str
    subject: str
    snippet: str
    from_address: str | None
    to_addresses: list[str]
    date_sent: datetime | None
    is_read: bool
    labels: list[str]
    body: str = ""

    @classmethod
    def from_entity(cls, email: Email) -> EmailDTO:
        return cls(
            id=str(email.id),
            message_id=email.message_id.value,
            thread_id=email.thread_id.value,
            subject=email.subject,
            snippet=email.snippet,
            from_address=email.from_address.value if email.from_address else None,
            to_addresses=[a.value for a in email.to_addresses],
            date_sent=email.date_sent,
            is_read=email.is_read,
            labels=sorted(email.labels),
            body=email.body,
        )

    @classmethod
    def from_gateway_header(cls, header: GmailMessageHeader) -> EmailDTO:
        date_sent = None
        if header.date:
            try:
                date_sent = email.utils.parsedate_to_datetime(header.date)
            except (ValueError, TypeError):
                pass
        return cls(
            id="",
            message_id=header.id,
            thread_id=header.thread_id,
            subject=header.subject,
            snippet=header.snippet,
            from_address=header.from_ or None,
            to_addresses=[],
            date_sent=date_sent,
            is_read="UNREAD" not in header.labels,
            labels=list(header.labels),
            body="",
        )

    @classmethod
    def from_gateway_message(cls, message: GmailMessage) -> EmailDTO:
        to_addresses = [a.strip() for a in message.to.split(",")] if message.to else []
        date_sent = None
        if message.date:
            try:
                date_sent = email.utils.parsedate_to_datetime(message.date)
            except (ValueError, TypeError):
                pass
        return cls(
            id="",
            message_id=message.id,
            thread_id=message.thread_id,
            subject=message.subject,
            snippet=message.snippet,
            from_address=message.from_ or None,
            to_addresses=to_addresses,
            date_sent=date_sent,
            is_read="UNREAD" not in message.labels,
            labels=list(message.labels),
            body=message.body,
        )


@dataclass(frozen=True)
class ThreadDTO:
    id: str
    thread_id: str
    subject: str
    snippet: str
    participants: list[str]
    email_ids: list[str]
    last_updated: datetime | None
    is_read: bool

    @classmethod
    def from_entity(cls, thread: Thread) -> ThreadDTO:
        return cls(
            id=str(thread.id),
            thread_id=thread.thread_id.value,
            subject=thread.subject,
            snippet=thread.snippet,
            participants=list(thread.participants),
            email_ids=[str(eid) for eid in thread.email_ids],
            last_updated=thread.last_updated,
            is_read=thread.is_read,
        )


@dataclass(frozen=True)
class LabelDTO:
    id: str
    label_id: str
    name: str
    color: str
    type: str
    is_system: bool

    @classmethod
    def from_entity(cls, label: Label) -> LabelDTO:
        return cls(
            id=str(label.id),
            label_id=label.label_id,
            name=label.name,
            color=label.color,
            type=label.type,
            is_system=label.is_system,
        )

    @classmethod
    def from_gateway_label(cls, label: GmailLabel) -> LabelDTO:
        return cls(
            id="",
            label_id=label.id,
            name=label.name,
            color=label.color or "",
            type=label.type,
            is_system=label.name in SYSTEM_LABELS,
        )


@dataclass(frozen=True)
class SearchEmailsResult:
    emails: list[EmailDTO] = field(default_factory=list)
    page: int = 1
    page_size: int = 25
    next_page_token: str | None = None
    total_estimate: int = 0
