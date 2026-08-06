"""Boundary parsing for MCP tool arguments.

Tool arguments arrive as untyped agent input. These helpers parse them into the
domain types the use cases expect and raise ``ValidationError`` on malformed
input, so every tool maps bad input to a structured ``invalid_input`` error
instead of letting a stdlib ``ValueError`` propagate.
"""

from __future__ import annotations

from datetime import UTC, date, datetime, time
from uuid import UUID

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId


def parse_uuid(value: str) -> UUIDId:
    try:
        return UUIDId(UUID(value))
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"invalid id: {value!r} is not a UUID") from exc


def parse_email_identifier(value: str) -> UUIDId | GmailMessageId:
    """A UUID resolves against the local cache; anything else is treated as a
    Gmail message id resolved against the live API."""
    try:
        return UUIDId(UUID(value))
    except (ValueError, TypeError):
        return GmailMessageId(value)


def parse_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError) as exc:
        raise ValidationError(f"invalid date: {value!r} (expected YYYY-MM-DD)") from exc


def parse_date_anchor(value: str | None) -> datetime | None:
    """Parse a ``YYYY-MM-DD`` date into a UTC-midnight datetime anchoring a
    digest window; ``None`` when unset."""
    parsed = parse_date(value)
    if parsed is None:
        return None
    return datetime.combine(parsed, time.min, tzinfo=UTC)
