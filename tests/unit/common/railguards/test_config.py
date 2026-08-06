from __future__ import annotations

import pytest

from agentic_mail_mcp.Bootstrap.Settings import RailguardsConfig
from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Common.Railguards.config import READ_ONLY, RailguardConfig


class TestRailguardConfig:
    def test_default_is_read_only(self) -> None:
        assert RailguardConfig().access_level == READ_ONLY
        assert RailguardConfig().is_read_only is True

    def test_from_settings_defaults_to_read_only(self) -> None:
        config = RailguardConfig.from_settings(RailguardsConfig())
        assert config.is_read_only is True
        assert config.archive_first_policy is False

    def test_invalid_access_level_rejected(self) -> None:
        with pytest.raises(ValidationError):
            RailguardConfig(access_level="owner")

    def test_from_settings_copies_all_fields(self) -> None:
        settings = RailguardsConfig(
            access_level="read_write",
            allowed_recipients=["a@b.com"],
            blocked_actions=["permanent_delete"],
            rate_limits={"forward": 5},
            archive_first_policy=True,
        )
        config = RailguardConfig.from_settings(settings)
        assert config.access_level == "read_write"
        assert config.allowed_recipients == ["a@b.com"]
        assert config.blocked_actions == ["permanent_delete"]
        assert config.rate_limits == {"forward": 5}
        assert config.archive_first_policy is True


class TestRecipientMatching:
    def test_empty_allowlist_allows_all(self) -> None:
        assert RailguardConfig(access_level="read_write").recipient_allowed("x@y.com")

    def test_exact_address_match(self) -> None:
        config = RailguardConfig(
            access_level="read_write", allowed_recipients=["alice@example.com"]
        )
        assert config.recipient_allowed("alice@example.com") is True
        assert config.recipient_allowed("bob@example.com") is False

    def test_domain_match(self) -> None:
        config = RailguardConfig(
            access_level="read_write", allowed_recipients=["@example.com"]
        )
        assert config.recipient_allowed("anyone@example.com") is True
        assert config.recipient_allowed("anyone@other.com") is False

    def test_matching_is_case_insensitive(self) -> None:
        config = RailguardConfig(
            access_level="read_write", allowed_recipients=["Alice@Example.com"]
        )
        assert config.recipient_allowed("alice@example.com") is True


class TestActionAndRateHelpers:
    def test_is_action_blocked(self) -> None:
        config = RailguardConfig(
            access_level="read_write", blocked_actions=["permanent_delete"]
        )
        assert config.is_action_blocked("permanent_delete") is True
        assert config.is_action_blocked("archive") is False

    def test_rate_limit_for(self) -> None:
        config = RailguardConfig(access_level="read_write", rate_limits={"forward": 3})
        assert config.rate_limit_for("forward") == 3
        assert config.rate_limit_for("archive") is None
