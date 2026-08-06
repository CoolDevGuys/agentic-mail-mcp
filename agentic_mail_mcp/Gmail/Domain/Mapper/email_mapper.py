from __future__ import annotations

from datetime import datetime
from email.utils import getaddresses, parseaddr

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailMessage
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
                date_sent = datetime.fromisoformat(
                    gateway_message.date.removesuffix("Z")
                )
            except (ValueError, AttributeError):
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
        )
