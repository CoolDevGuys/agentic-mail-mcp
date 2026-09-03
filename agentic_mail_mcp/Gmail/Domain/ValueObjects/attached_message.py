from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from agentic_mail_mcp.Gmail.Domain.ValueObjects.email_address import EmailAddress


@dataclass(frozen=True)
class AttachedMessage:
    """A nested ``message/rfc822`` part — the original of a forwarded email."""

    subject: str
    from_address: EmailAddress | None
    date_sent: datetime | None
    body: str
