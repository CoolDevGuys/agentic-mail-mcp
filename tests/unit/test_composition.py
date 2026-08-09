from __future__ import annotations

import asyncio

import pytest

from agentic_mail_mcp.Bootstrap.Composition import (
    build_resource_context,
    build_use_cases,
)
from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.MCP.Server import create_server
from tests.fakes.ports import StubGmailGateway

_READ = {"search_emails", "get_email", "get_thread", "list_unread", "list_labels"}
_WRITE = {
    "forward_email",
    "archive_email",
    "delete_email",
    "create_draft",
    "send_draft",
    "add_label",
}
_INTEL = {
    "summarize_email",
    "classify_email",
    "suggest_reply",
    "extract_action_items",
    "daily_digest",
    "weekly_digest",
}


@pytest.fixture
def settings(tmp_path, monkeypatch) -> Settings:
    monkeypatch.setenv(
        "AGENTIC_MAIL_MCP_DATABASE_URL", f"sqlite:///{tmp_path / 't.db'}"
    )
    monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY", "test-key")
    monkeypatch.setenv(
        "AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH", str(tmp_path / "token.json")
    )
    return Settings.from_env()


class TestBuildUseCases:
    def test_core_use_cases_always_wired(self, settings) -> None:
        uses = build_use_cases(settings, gateway=StubGmailGateway())

        assert uses.search_emails is not None
        assert uses.forward_email is not None

    def test_caller_first_no_intelligence_tools_without_llm(self, settings) -> None:
        # No LLM configured -> per-email intelligence stays caller-side (prompts),
        # digests are not wired either.
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        assert uses.summarize_email is None
        assert uses.daily_digest is None

    def test_digests_wired_when_llm_configured(self, settings, monkeypatch) -> None:
        monkeypatch.setenv("AGENTIC_MAIL_MCP_LLM_API_KEY", "sk-real")
        settings = Settings.from_env()
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        assert uses.daily_digest is not None
        assert uses.weekly_digest is not None
        # per-email tools stay off unless explicitly opted in
        assert uses.summarize_email is None

    def test_internal_tools_opt_in_wires_per_email(self, settings, monkeypatch) -> None:
        monkeypatch.setenv("AGENTIC_MAIL_MCP_LLM_API_KEY", "sk-real")
        monkeypatch.setenv("AGENTIC_MAIL_MCP_LLM_INTERNAL_TOOLS", "true")
        settings = Settings.from_env()
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        assert uses.summarize_email is not None
        assert uses.classify_email is not None

    def test_search_skipped_without_backend(self, settings) -> None:
        # sqlite-vec is not installed in the default test env, so search is skipped
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        try:
            import pysqlite3  # noqa: F401
            import sqlite_vec  # noqa: F401
        except ImportError:
            assert uses.semantic_search is None
        else:
            # Backend is available — search use case is built
            assert uses.semantic_search is not None


class TestServerExposesTools:
    def test_read_write_registered_under_read_write(
        self, settings, monkeypatch
    ) -> None:
        monkeypatch.setenv("AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL", "read_write")
        settings = Settings.from_env()
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        server = create_server(use_cases=uses, settings=settings)

        names = {t.name for t in asyncio.run(server.list_tools())}

        assert _READ <= names
        assert _WRITE <= names
        # caller-first: no internal intelligence tools without an LLM
        assert names.isdisjoint(_INTEL)

    def test_write_tools_hidden_under_read_only(self, settings) -> None:
        # default access level is read_only
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        server = create_server(use_cases=uses, settings=settings)

        names = {t.name for t in asyncio.run(server.list_tools())}

        assert _READ <= names
        assert names.isdisjoint(_WRITE)

    def test_intelligence_prompts_always_available(self, settings) -> None:
        uses = build_use_cases(settings, gateway=StubGmailGateway())
        server = create_server(use_cases=uses, settings=settings)

        prompts = {p.name for p in asyncio.run(server.list_prompts())}

        assert {"summarize_email", "classify_email", "draft_reply"} <= prompts


class TestBringYourOwnClientConfig:
    """Users supply their own Google OAuth app — via a downloaded credentials
    file or explicit id/secret."""

    def test_from_client_id_and_secret(self, settings, monkeypatch) -> None:
        from agentic_mail_mcp.Bootstrap.Composition import resolve_client_config

        monkeypatch.setenv(
            "AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID", "abc.apps.googleusercontent.com"
        )
        monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET", "secret")

        config = resolve_client_config(Settings.from_env())

        assert config["installed"]["client_id"].startswith("abc")

    def test_from_downloaded_credentials_file(
        self, settings, tmp_path, monkeypatch
    ) -> None:
        import json

        from agentic_mail_mcp.Bootstrap.Composition import resolve_client_config

        creds = tmp_path / "credentials.json"
        creds.write_text(
            json.dumps({"installed": {"client_id": "xyz", "client_secret": "s"}})
        )
        monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE", str(creds))

        config = resolve_client_config(Settings.from_env())

        assert config["installed"]["client_id"] == "xyz"

    def test_file_takes_precedence_over_id_secret(
        self, settings, tmp_path, monkeypatch
    ) -> None:
        import json

        from agentic_mail_mcp.Bootstrap.Composition import resolve_client_config

        creds = tmp_path / "credentials.json"
        creds.write_text(json.dumps({"installed": {"client_id": "from-file"}}))
        monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE", str(creds))
        monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID", "from-env")
        monkeypatch.setenv("AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET", "s")

        config = resolve_client_config(Settings.from_env())

        assert config["installed"]["client_id"] == "from-file"

    def test_none_when_nothing_configured(self, settings) -> None:
        from agentic_mail_mcp.Bootstrap.Composition import resolve_client_config

        assert resolve_client_config(settings) is None

    def test_resource_context_reports_access_level(self, settings) -> None:
        ctx = build_resource_context(settings)
        assert ctx.access_level == "read_only"
