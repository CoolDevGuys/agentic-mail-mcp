from __future__ import annotations

import json

import pytest

from agentic_mail_mcp.Bootstrap.auth_check import check_auth
from agentic_mail_mcp.Bootstrap.Settings import GmailConfig, Settings
from agentic_mail_mcp.Gmail.Infrastructure.Google.oauth_provider import (
    GmailOAuthProvider,
)

_KEY = "unit-test-encryption-key"


def _settings(tmp_path, *, client=True, key=True, token=True) -> Settings:
    token_path = tmp_path / "token.enc"
    gmail = GmailConfig(
        oauth_client_id="id" if client else "",
        oauth_client_secret="secret" if client else "",
        token_encryption_key=_KEY if key else "",
        token_storage_path=str(token_path),
    )
    if token:
        # Store a real encrypted token so has_token() and load_credentials() work.
        provider = GmailOAuthProvider(str(token_path), _KEY)
        provider.save_token(
            json.dumps(
                {"client_id": "id", "client_secret": "secret", "refresh_token": "r"}
            )
        )
    return Settings(gmail=gmail)


class _OkGateway:
    def get_profile(self) -> str:
        return "user@example.com"


def _boom(message: str):
    def factory(_credentials):
        raise RuntimeError(message)

    return factory


def _must_not_run(_credentials):
    raise AssertionError("gateway_factory should not be called for this stage")


class TestCheckAuth:
    def test_success_returns_account(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path), gateway_factory=lambda _c: _OkGateway()
        )
        assert result.ok is True
        assert result.stage == "ok"
        assert result.account == "user@example.com"
        assert "user@example.com" in result.message

    def test_no_client(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path, client=False, token=False),
            gateway_factory=_must_not_run,
        )
        assert (result.ok, result.stage) == (False, "no_client")

    def test_no_key(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path, key=False, token=False),
            gateway_factory=_must_not_run,
        )
        assert (result.ok, result.stage) == (False, "no_key")

    def test_no_token(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path, token=False), gateway_factory=_must_not_run
        )
        assert (result.ok, result.stage) == (False, "no_token")
        assert "auth" in result.message

    def test_token_rejected(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path),
            gateway_factory=_boom("invalid_grant: Token has been expired or revoked"),
        )
        assert (result.ok, result.stage) == (False, "token_rejected")
        assert "auth" in result.message

    def test_unreachable(self, tmp_path) -> None:
        result = check_auth(
            _settings(tmp_path),
            gateway_factory=_boom("Connection refused"),
        )
        assert (result.ok, result.stage) == (False, "unreachable")


@pytest.mark.parametrize(
    "exc,expected",
    [
        (RuntimeError("invalid_grant"), True),
        (RuntimeError("Unauthorized"), True),
        (RuntimeError("token revoked"), True),
        (RuntimeError("Connection reset by peer"), False),
        (RuntimeError("timed out"), False),
    ],
)
def test_auth_error_classification(tmp_path, exc, expected) -> None:
    def factory(_credentials):
        raise exc

    result = check_auth(_settings(tmp_path), gateway_factory=factory)
    assert (result.stage == "token_rejected") is expected
