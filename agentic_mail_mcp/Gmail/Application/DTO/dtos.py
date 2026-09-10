from __future__ import annotations

import email.utils
from dataclasses import dataclass, field
from datetime import datetime

from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Entities.label import SYSTEM_LABELS, Label
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailAttachedMessage,
    GmailLabel,
    GmailMessage,
    GmailMessageHeader,
    GmailThread,
)
from agentic_mail_mcp.Gmail.Domain.ValueObjects.attached_message import AttachedMessage

# Zero-width spaces/joiners, bidi controls, soft hyphen, and BOM — injected by
# some senders (e.g. LinkedIn) and invisible when rendered, but corrupting for
# programmatic snippet parsing.
_INVISIBLE_CHARS = frozenset(
    "\u00ad\u200b\u200c\u200d\u200e\u200f\u2060\u2061\u2062\u2063\u2064\ufeff"
)


def _clean_snippet(text: str, max_length: int) -> str:
    """Strip invisible characters, collapse whitespace, truncate with an
    ellipsis when ``max_length`` is exceeded."""
    stripped = "".join(ch for ch in text if ch not in _INVISIBLE_CHARS)
    collapsed = " ".join(stripped.split())
    if len(collapsed) <= max_length:
        return collapsed
    return collapsed[:max_length].rstrip() + "…"


def derive_snippet(body: str, fallback: str, max_length: int = 200) -> str:
    """Derive a short one-line snippet from the body.

    Falls back to the gateway-provided snippet when the body is empty. Either
    source is cleaned of invisible characters, whitespace-collapsed to a single
    line, and truncated with an ellipsis when it exceeds ``max_length``.
    """
    return _clean_snippet(body or fallback, max_length)


def _split_sender(raw: str) -> tuple[str | None, str | None]:
    """Split a raw ``From`` header into ``(bare address, display name)``.

    Senders like LinkedIn InMail put the real person only in the display name
    (``"Will G. <inmail-hit-reply@linkedin.com>"``); exposing both parts saves
    callers from parsing the header. Malformed values without a parseable
    address are kept verbatim so no information is lost.
    """
    if not raw:
        return None, None
    name, address = email.utils.parseaddr(raw)
    if not address:
        return raw.strip() or None, None
    return address, name.strip() or None


@dataclass(frozen=True)
class AttachedMessageDTO:
    """A nested ``message/rfc822`` part — the original of a forwarded email."""

    subject: str
    from_address: str | None
    date_sent: datetime | None
    body: str

    @classmethod
    def from_gateway(cls, attached: GmailAttachedMessage) -> AttachedMessageDTO:
        date_sent = None
        if attached.date:
            try:
                date_sent = email.utils.parsedate_to_datetime(attached.date)
            except (ValueError, TypeError):
                pass
        return cls(
            subject=attached.subject,
            from_address=attached.from_ or None,
            date_sent=date_sent,
            body=attached.body,
        )

    @classmethod
    def from_domain(cls, attached: AttachedMessage) -> AttachedMessageDTO:
        return cls(
            subject=attached.subject,
            from_address=(
                attached.from_address.value if attached.from_address else None
            ),
            date_sent=attached.date_sent,
            body=attached.body,
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
    # Sender display name from the raw From header (live gateway paths only —
    # the aggregate stores just the address), e.g. the real person behind a
    # LinkedIn InMail alias address.
    from_display_name: str | None = None
    body: str = ""
    # The original(s) of a forward (nested message/rfc822 parts), each with its
    # own subject, sender, date, and body. Empty for non-forwarded messages.
    attached_messages: list[AttachedMessageDTO] = field(default_factory=list)

    @classmethod
    def from_entity(cls, email: Email) -> EmailDTO:
        return cls(
            # The Gmail message id is the stable identity across read and write
            # tools; the internal cache UUID is not exposed to callers.
            id=email.message_id.value,
            message_id=email.message_id.value,
            thread_id=email.thread_id.value,
            subject=email.subject,
            snippet=derive_snippet(email.body, email.snippet),
            from_address=email.from_address.value if email.from_address else None,
            to_addresses=[a.value for a in email.to_addresses],
            date_sent=email.date_sent,
            is_read=email.is_read,
            labels=sorted(email.labels),
            body=email.body,
            attached_messages=[
                AttachedMessageDTO.from_domain(a) for a in email.attached_messages
            ],
        )

    @classmethod
    def from_gateway_header(cls, header: GmailMessageHeader) -> EmailDTO:
        date_sent = None
        if header.date:
            try:
                date_sent = email.utils.parsedate_to_datetime(header.date)
            except (ValueError, TypeError):
                pass
        to_addresses = (
            [a.strip() for a in header.to.split(",")] if header.to else []
        )
        return cls(
            # No internal cache UUID exists for a live (non-cached) result, so
            # the Gmail message id doubles as the identifier — it is what
            # get_email actually accepts, unlike an empty string.
            id=header.id,
            message_id=header.id,
            thread_id=header.thread_id,
            subject=header.subject,
            snippet=derive_snippet(header.body, header.snippet),
            from_address=_split_sender(header.from_)[0],
            from_display_name=_split_sender(header.from_)[1],
            to_addresses=to_addresses,
            date_sent=date_sent,
            is_read="UNREAD" not in header.labels,
            labels=list(header.labels),
            body=header.body,
            attached_messages=[
                AttachedMessageDTO.from_gateway(a) for a in header.attached_messages
            ],
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
            id=message.id,
            message_id=message.id,
            thread_id=message.thread_id,
            subject=message.subject,
            snippet=derive_snippet(message.body, message.snippet),
            from_address=_split_sender(message.from_)[0],
            from_display_name=_split_sender(message.from_)[1],
            to_addresses=to_addresses,
            date_sent=date_sent,
            is_read="UNREAD" not in message.labels,
            labels=list(message.labels),
            body=message.body,
            attached_messages=[
                AttachedMessageDTO.from_gateway(a) for a in message.attached_messages
            ],
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
    # Full messages in thread order, each with its own body, resolved live from
    # Gmail (see from_gateway_thread).
    emails: list[EmailDTO] = field(default_factory=list)

    @classmethod
    def from_gateway_thread(cls, thread: GmailThread) -> ThreadDTO:
        emails = [EmailDTO.from_gateway_message(m) for m in thread.messages]
        participants = sorted(
            {e.from_address for e in emails if e.from_address}
            | {addr for e in emails for addr in e.to_addresses}
        )
        last_updated = max((e.date_sent for e in emails if e.date_sent), default=None)
        return cls(
            id="",
            thread_id=thread.id,
            # Gmail threads carry no thread-level subject; the first message's
            # subject stands in, matching how Gmail's own UI titles a thread.
            subject=emails[0].subject if emails else "",
            snippet=thread.snippet,
            participants=participants,
            email_ids=[e.message_id for e in emails],
            last_updated=last_updated,
            is_read=all(e.is_read for e in emails) if emails else True,
            emails=emails,
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
    # Exact number of messages matching the query (after any seen_ids
    # exclusion), not Gmail's approximate resultSizeEstimate.
    total_count: int = 0
