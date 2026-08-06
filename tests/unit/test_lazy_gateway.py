from __future__ import annotations

import pytest

from src.Common.Domain.Exceptions import DomainError
from src.Gmail.Infrastructure.Google.lazy_gateway import LazyGmailGateway
from tests.fakes.ports import StubGmailGateway


class _FakeOAuth:
    def __init__(self, has_token: bool) -> None:
        self._has_token = has_token
        self.loaded = False

    def has_token(self) -> bool:
        return self._has_token

    def load_credentials(self):
        self.loaded = True
        return object()


class TestLazyGmailGateway:
    def test_raises_clear_error_when_not_authorized(self) -> None:
        gw = LazyGmailGateway(_FakeOAuth(has_token=False))

        with pytest.raises(DomainError) as exc:
            gw.list_labels()

        assert "gmail-mcp-server auth" in str(exc.value)

    def test_builds_and_delegates_when_authorized(self) -> None:
        stub = StubGmailGateway()
        oauth = _FakeOAuth(has_token=True)
        gw = LazyGmailGateway(oauth, gateway_factory=lambda creds: stub)

        gw.modify_message("m1", ["INBOX"], [])
        gw.trash_message("m1")

        assert oauth.loaded is True
        assert stub.modify_calls == [("m1", ["INBOX"], [])]
        assert stub.trashed == ["m1"]

    def test_builds_backend_only_once(self) -> None:
        stub = StubGmailGateway()
        calls = {"n": 0}

        def factory(creds):
            calls["n"] += 1
            return stub

        gw = LazyGmailGateway(_FakeOAuth(has_token=True), gateway_factory=factory)
        gw.list_labels()
        gw.list_labels()

        assert calls["n"] == 1
