from __future__ import annotations

import os

import pytest

from agentic_mail_mcp.Bootstrap import cli
from agentic_mail_mcp.Bootstrap.Settings import Settings


class _FakeProvider:
    def __init__(self) -> None:
        self.authorized = False

    def authorize_interactive(self) -> str:
        self.authorized = True
        return "{}"


def _settings(**env) -> Settings:
    # build a Settings with explicit sections (env isolation is handled by the
    # autouse conftest fixture)
    from agentic_mail_mcp.Bootstrap.Settings import GmailConfig

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
        from agentic_mail_mcp.Common.Domain.Exceptions import DomainError

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
    def test_no_subcommand_shows_help_and_does_not_serve(
        self, monkeypatch, capsys
    ) -> None:
        called = {}
        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp"])
        monkeypatch.setattr(
            cli, "_serve", lambda settings: called.setdefault("serve", True)
        )
        monkeypatch.setattr(
            cli, "_auth", lambda settings: called.setdefault("auth", True)
        )

        cli.main()

        assert called == {}  # the server is never started implicitly
        out = capsys.readouterr().out
        # help lists the available subcommands
        for cmd in ("serve", "auth", "init", "verify-auth"):
            assert cmd in out

    def test_init_command_dispatches(self, monkeypatch) -> None:
        called = {}

        def fake_init(*, env_path) -> int:
            called["init"] = True
            return 0

        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp", "init"])
        monkeypatch.setattr(cli, "run_init", fake_init)
        monkeypatch.setattr(
            cli, "_serve", lambda settings: called.setdefault("serve", True)
        )

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 0
        assert called == {"init": True}

    def test_auth_command_dispatches(self, monkeypatch) -> None:
        called = {}
        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp", "auth"])
        monkeypatch.setattr(
            cli, "_serve", lambda settings: called.setdefault("serve", True)
        )
        monkeypatch.setattr(
            cli, "_auth", lambda settings: called.setdefault("auth", True)
        )

        cli.main()

        assert called == {"auth": True}


class TestVerifyAuth:
    def _result(self, ok: bool):
        from agentic_mail_mcp.Bootstrap.auth_check import AuthCheckResult

        return AuthCheckResult(
            ok=ok,
            stage="ok" if ok else "token_rejected",
            message="Authorized as me@example.com."
            if ok
            else "token expired — re-auth",
            account="me@example.com" if ok else None,
        )

    def test_success_exits_zero(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp", "verify-auth"])
        monkeypatch.setattr(cli, "check_auth", lambda settings: self._result(True))
        monkeypatch.setattr(cli, "setup_logging", lambda **kwargs: None)

        cli.main()  # no SystemExit on success

        assert "me@example.com" in capsys.readouterr().out

    def test_failure_exits_nonzero(self, monkeypatch, capsys) -> None:
        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp", "verify-auth"])
        monkeypatch.setattr(cli, "check_auth", lambda settings: self._result(False))
        monkeypatch.setattr(cli, "setup_logging", lambda **kwargs: None)

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 1
        assert "re-auth" in capsys.readouterr().err


class TestServePreflight:
    def _stub_serve_collaborators(self, monkeypatch, run_calls) -> None:
        class _Container:
            def singleton(self, *a, **k) -> None:
                pass

        monkeypatch.setattr(
            cli.Container, "with_defaults", lambda settings: _Container()
        )
        monkeypatch.setattr(cli, "build_use_cases", lambda settings: object())
        monkeypatch.setattr(cli, "build_resource_context", lambda settings: object())
        monkeypatch.setattr(cli, "create_server", lambda container: object())
        monkeypatch.setattr(
            cli, "run_server", lambda server, settings: run_calls.append(True)
        )

    def _http_settings(self):
        from agentic_mail_mcp.Bootstrap.Settings import MCPConfig

        return Settings(mcp=MCPConfig(transport="http"))

    def test_http_startup_runs_check_and_continues_on_failure(
        self, monkeypatch
    ) -> None:
        from agentic_mail_mcp.Bootstrap.auth_check import AuthCheckResult

        checks, runs = [], []
        self._stub_serve_collaborators(monkeypatch, runs)

        def spy(settings):
            checks.append(True)
            return AuthCheckResult(ok=False, stage="no_token", message="run auth")

        monkeypatch.setattr(cli, "check_auth", spy)

        cli._serve(self._http_settings())

        assert checks == [True]  # preflight ran
        assert runs == [True]  # server still started despite failure

    def test_stdio_startup_skips_check(self, monkeypatch) -> None:
        checks, runs = [], []
        self._stub_serve_collaborators(monkeypatch, runs)
        monkeypatch.setattr(cli, "check_auth", lambda settings: checks.append(True))

        cli._serve(Settings())  # default transport = stdio

        assert checks == []  # network check not performed for stdio
        assert runs == [True]


class TestEnvFile:
    def test_missing_env_file_exits(self, tmp_path) -> None:
        with pytest.raises(SystemExit) as exc:
            cli._load_env_file(str(tmp_path / "nope.env"))
        assert exc.value.code == 1

    def test_load_env_file_populates_environment(self, tmp_path) -> None:
        f = tmp_path / "custom.env"
        f.write_text("AGENTIC_MAIL_MCP_MCP_PORT=7799\n")
        try:
            cli._load_env_file(str(f))
            assert os.environ.get("AGENTIC_MAIL_MCP_MCP_PORT") == "7799"
        finally:
            os.environ.pop("AGENTIC_MAIL_MCP_MCP_PORT", None)

    def test_serve_loads_env_file_into_settings(self, tmp_path, monkeypatch) -> None:
        f = tmp_path / "s.env"
        f.write_text("AGENTIC_MAIL_MCP_MCP_PORT=7799\n")
        captured = {}
        monkeypatch.setattr(
            cli.sys, "argv", ["agentic-mail-mcp", "serve", "--env-file", str(f)]
        )
        monkeypatch.setattr(
            cli, "_serve", lambda settings: captured.setdefault("s", settings)
        )
        monkeypatch.setattr(cli, "setup_logging", lambda **kwargs: None)
        try:
            cli.main()
            assert captured["s"].mcp.port == 7799
        finally:
            os.environ.pop("AGENTIC_MAIL_MCP_MCP_PORT", None)

    def test_env_file_from_environment_variable(self, tmp_path, monkeypatch) -> None:
        f = tmp_path / "e.env"
        f.write_text("AGENTIC_MAIL_MCP_MCP_PORT=7788\n")
        captured = {}
        monkeypatch.setenv("AGENTIC_MAIL_MCP_ENV_FILE", str(f))
        monkeypatch.setattr(cli.sys, "argv", ["agentic-mail-mcp", "serve"])
        monkeypatch.setattr(
            cli, "_serve", lambda settings: captured.setdefault("s", settings)
        )
        monkeypatch.setattr(cli, "setup_logging", lambda **kwargs: None)
        try:
            cli.main()
            assert captured["s"].mcp.port == 7788
        finally:
            os.environ.pop("AGENTIC_MAIL_MCP_MCP_PORT", None)

    def test_init_env_file_sets_output_path(self, monkeypatch) -> None:
        captured = {}

        def fake_init(*, env_path) -> int:
            captured["path"] = env_path
            return 0

        monkeypatch.setattr(
            cli.sys, "argv", ["agentic-mail-mcp", "init", "--env-file", "/tmp/out.env"]
        )
        monkeypatch.setattr(cli, "run_init", fake_init)

        with pytest.raises(SystemExit) as exc:
            cli.main()

        assert exc.value.code == 0
        assert str(captured["path"]) == "/tmp/out.env"
