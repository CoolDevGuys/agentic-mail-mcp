from __future__ import annotations

from datetime import UTC, date, datetime
from uuid import uuid4

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId
from agentic_mail_mcp.MCP.Tools.arguments import (
    parse_date,
    parse_date_anchor,
    parse_email_identifier,
    parse_uuid,
)


class TestParseUuid:
    def test_valid_uuid(self) -> None:
        raw = str(uuid4())
        assert parse_uuid(raw) == UUIDId.from_string(raw)

    def test_malformed_uuid_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            parse_uuid("not-a-uuid")


class TestParseEmailIdentifier:
    def test_uuid_resolves_to_uuidid(self) -> None:
        raw = str(uuid4())
        assert isinstance(parse_email_identifier(raw), UUIDId)

    def test_non_uuid_resolves_to_gmail_message_id(self) -> None:
        result = parse_email_identifier("18f9a1b2c3")
        assert isinstance(result, GmailMessageId)
        assert result.value == "18f9a1b2c3"

    def test_empty_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            parse_email_identifier("")


class TestParseDate:
    def test_none_and_empty_return_none(self) -> None:
        assert parse_date(None) is None
        assert parse_date("") is None

    def test_valid_date(self) -> None:
        assert parse_date("2026-07-01") == date(2026, 7, 1)

    def test_malformed_date_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            parse_date("07/01/2026")


class TestParseDateAnchor:
    def test_none_returns_none(self) -> None:
        assert parse_date_anchor(None) is None

    def test_returns_utc_midnight(self) -> None:
        assert parse_date_anchor("2026-07-01") == datetime(2026, 7, 1, tzinfo=UTC)

    def test_malformed_raises_validation_error(self) -> None:
        with pytest.raises(ValidationError):
            parse_date_anchor("nope")
