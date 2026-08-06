from __future__ import annotations

from agentic_mail_mcp.MCP.Resources import (
    ACCOUNT_URI,
    INDEX_URI,
    WATCH_URI,
    ResourceContext,
    build_resources,
)


def _resource(context, uri):
    return next(r for r in build_resources(context) if r.uri == uri)


class TestResources:
    def test_account_info_reports_access_level(self) -> None:
        context = ResourceContext(
            account_email="me@example.com", access_level="read_write"
        )
        payload = _resource(context, ACCOUNT_URI).read()
        assert payload == {"email": "me@example.com", "access_level": "read_write"}

    def test_watch_status_default_inactive(self) -> None:
        context = ResourceContext(
            account_email="me@example.com", access_level="read_only"
        )
        payload = _resource(context, WATCH_URI).read()
        assert payload["active"] is False

    def test_watch_status_uses_provider(self) -> None:
        context = ResourceContext(
            account_email="me@example.com",
            access_level="read_only",
            watch_status_provider=lambda: {"active": True, "history_id": "42"},
        )
        payload = _resource(context, WATCH_URI).read()
        assert payload == {"active": True, "history_id": "42"}

    def test_index_status_reports_count(self) -> None:
        context = ResourceContext(
            account_email="me@example.com",
            access_level="read_only",
            index_count_provider=lambda: 7,
        )
        payload = _resource(context, INDEX_URI).read()
        assert payload == {"document_count": 7}

    def test_three_resources_registered(self) -> None:
        context = ResourceContext(
            account_email="me@example.com", access_level="read_only"
        )
        uris = {r.uri for r in build_resources(context)}
        assert uris == {ACCOUNT_URI, WATCH_URI, INDEX_URI}
