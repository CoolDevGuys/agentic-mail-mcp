from __future__ import annotations

import pytest

from src.Bootstrap import cli
from src.Bootstrap.Settings import Settings


class _FakeProvider:
    def __init__(self) -> None:
        self.authorized = False

    def authorize_interactive(self) -> str:
        self.authorized = True
        return "{}"


def _settings(**env) -> Settings:
    # build a Settings with explicit sections (env isolation is handled by the
    # autouse conftest fixture)
    from src.Bootstrap.Settings import GmailConfig

    return Settings(gmail=GmailConfig(**env))


class TestAuthCommand:
    def test_missing_client_id_exits(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            cli._auth(_settings(oauth_client_id="", oauth_client_secret="s"))
        assert exc.value.code == 1
        assert "OAUTH_CLIENT_ID" in capsys.readouterr().err

    def test_missing_encryption_key_exits(self, capsys) -> None:
        with pytest.raises(SystemExit) as exc:
            cli._auth(
                _settings(
                    oauth_client_id="id",
                    oauth_client_secret="s",
                    token_encryption_key="",
                )
            )
        assert exc.value.code == 1
        assert "ENCRYPTION_KEY" in capsys.readouterr().err

    def test_accepts_downloaded_credentials_file(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        creds = tmp_path / "credentials.json"
        creds.write_text('{"installed": {"client_id": "x", "client_secret": "y"}}')
        fake = _FakeProvider()
        monkeypatch.setattr(cli, "build_oauth_provider", lambda settings: fake)

        cli._auth(
            _settings(
                client_secrets_file=str(creds),
                token_encryption_key="key",
                token_storage_path=str(tmp_path / "t.enc"),
            )
        )

        assert fake.authorized is True

    def test_runs_interactive_authorization(self, monkeypatch, capsys) -> None:
        fake = _FakeProvider()
        monkeypatch.setattr(cli, "build_oauth_provider", lambda settings: fake)

        cli._auth(
            _settings(
                oauth_client_id="id",
                oauth_client_secret="s",
                token_encryption_key="key",
                token_storage_path="/tmp/token.json",
            )
        )

        assert fake.authorized is True
        assert "Authorized" in capsys.readouterr().out

    def test_canceled_or_denied_exits_with_guidance(self, monkeypatch, capsys) -> None:
        from src.Common.Domain.Exceptions import DomainError

        class _Denied:
            def authorize_interactive(self) -> str:
                raise DomainError("Google authorization did not complete — canceled")

        monkeypatch.setattr(cli, "build_oauth_provider", lambda settings: _Denied())

        with pytest.raises(SystemExit) as exc:
            cli._auth(
                _settings(
                    oauth_client_id="id",
                    oauth_client_secret="s",
                    token_encryption_key="key",
                )
            )

        assert exc.value.code == 1
        err = capsys.readouterr().err
        assert "did not complete" in err
        assert "Test users" in err  # actionable guidance

    def test_keyboard_interrupt_exits_cleanly(self, monkeypatch, capsys) -> None:
        class _Interrupted:
            def authorize_interactive(self) -> str:
                raise KeyboardInterrupt

        monkeypatch.setattr(
            cli, "build_oauth_provider", lambda settings: _Interrupted()
        )

        with pytest.raises(SystemExit) as exc:
            cli._auth(
                _settings(
                    oauth_client_id="id",
                    oauth_client_secret="s",
                    token_encryption_key="key",
                )
            )

        assert exc.value.code == 1
        assert "canceled" in capsys.readouterr().err


class TestArgparse:
    def test_default_command_is_serve(self, monkeypatch) -> None:
        called = {}
        monkeypatch.setattr(cli.sys, "argv", ["gmail-mcp-server"])
        monkeypatch.setattr(
            cli, "_serve", lambda settings: called.setdefault("serve", True)
        )
        monkeypatch.setattr(
            cli, "_auth", lambda settings: called.setdefault("auth", True)
        )

        cli.main()

        assert called == {"serve": True}

    def test_auth_command_dispatches(self, monkeypatch) -> None:
        called = {}
        monkeypatch.setattr(cli.sys, "argv", ["gmail-mcp-server", "auth"])
        monkeypatch.setattr(
            cli, "_serve", lambda settings: called.setdefault("serve", True)
        )
        monkeypatch.setattr(
            cli, "_auth", lambda settings: called.setdefault("auth", True)
        )

        cli.main()

        assert called == {"auth": True}
