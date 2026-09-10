from __future__ import annotations

from email.utils import getaddresses, parseaddr, parsedate_to_datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailAttachedMessage,
    GmailMessage,
)
from agentic_mail_mcp.Gmail.Domain.ValueObjects.attached_message import AttachedMessage
from agentic_mail_mcp.Gmail.Domain.ValueObjects.email_address import EmailAddress


def _valid_address(raw: str) -> str | None:
    """Extract a bare, valid address from an RFC 5322 header value.

    Gmail headers carry display names (``"Name <a@b.com>"``); this pulls out the
    address. Anything that is not a valid address becomes ``None`` rather than
    breaking the whole mapping — real inboxes contain malformed senders.
    """
    address = parseaddr(raw or "")[1]
    if not address:
        return None
    try:
        EmailAddress(address)
    except ValidationError:
        return None
    return address


class EmailMapper:
    @staticmethod
    def to_domain(gateway_message: GmailMessage) -> Email:
        from_address = _valid_address(gateway_message.from_)
        to_addresses = [
            addr
            for _, raw in getaddresses([gateway_message.to or ""])
            if (addr := _valid_address(raw)) is not None
        ]

        date_sent = None
        if gateway_message.date:
            try:
                date_sent = parsedate_to_datetime(gateway_message.date)
            except (ValueError, TypeError):
                date_sent = None

        return Email.from_gmail_message(
            message_id=gateway_message.id,
            thread_id=gateway_message.thread_id,
            snippet=gateway_message.snippet,
            subject=gateway_message.subject,
            from_address=from_address,
            to_addresses=to_addresses,
            date_sent=date_sent,
            body=gateway_message.body,
            labels=gateway_message.labels,
            attached_messages=[
                _to_attached(attached) for attached in gateway_message.attached_messages
            ],
        )


def _to_attached(attached: GmailAttachedMessage) -> AttachedMessage:
    date_sent = None
    if attached.date:
        try:
            date_sent = parsedate_to_datetime(attached.date)
        except (ValueError, TypeError):
            date_sent = None
    return AttachedMessage(
        subject=attached.subject,
        from_address=EmailAddress(addr) if (addr := _valid_address(attached.from_)) else None,
        date_sent=date_sent,
        body=attached.body,
    )
