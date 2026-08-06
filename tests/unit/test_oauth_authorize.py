from __future__ import annotations

import json

import pytest

from src.Common.Domain.Exceptions import DomainError
from src.Gmail.Infrastructure.Google.oauth_provider import GmailOAuthProvider

_CLIENT_CONFIG = {"installed": {"client_id": "id", "client_secret": "s"}}


def _provider(tmp_path) -> GmailOAuthProvider:
    return GmailOAuthProvider(
        str(tmp_path / "token.enc"),
        "test-encryption-key",
        client_config=_CLIENT_CONFIG,
    )


class _FakeFlow:
    def __init__(
        self, *, raises: Exception | None = None, creds_json: str = "{}"
    ) -> None:
        self._raises = raises
        self._creds_json = creds_json

    def run_local_server(self, port: int = 0):
        if self._raises is not None:
            raise self._raises
        return _FakeCreds(self._creds_json)


class _FakeCreds:
    def __init__(self, payload: str) -> None:
        self._payload = payload

    def to_json(self) -> str:
        return self._payload


class TestAuthorizeInteractive:
    def test_missing_client_config_raises(self, tmp_path) -> None:
        provider = GmailOAuthProvider(
            str(tmp_path / "t.enc"), "key", client_config=None
        )
        with pytest.raises(DomainError, match="client_config"):
            provider.authorize_interactive()

    def test_canceled_flow_maps_to_domain_error_and_saves_nothing(
        self, tmp_path
    ) -> None:
        provider = _provider(tmp_path)

        with pytest.raises(DomainError, match="canceled or denied"):
            provider.authorize_interactive(
                flow_factory=lambda cfg, scopes: _FakeFlow(
                    raises=RuntimeError("access_denied")
                )
            )

        assert provider.has_token() is False  # no token written on failure

    def test_successful_flow_saves_encrypted_token(self, tmp_path) -> None:
        provider = _provider(tmp_path)
        payload = json.dumps({"refresh_token": "rt", "token": "at"})

        returned = provider.authorize_interactive(
            flow_factory=lambda cfg, scopes: _FakeFlow(creds_json=payload)
        )

        assert returned == payload
        assert provider.has_token() is True
        # round-trips through the encrypted store
        assert json.loads(provider.load_token())["refresh_token"] == "rt"
