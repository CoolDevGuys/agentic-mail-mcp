"""End-to-end MCP session tests (Phase 8.8).

Drive the assembled server through full tool flows over the MCP boundary, with
Gmail mocked at the gateway seam, and assert railguard enforcement end to end.
"""

from __future__ import annotations

from .conftest import build_session, seed_inbox_message, tool_json

_WRITE_TOOLS = {
    "forward_email",
    "archive_email",
    "delete_email",
    "create_draft",
    "send_draft",
    "add_label",
}


class TestReadWriteFlow:
    async def test_search_read_forward_archive_delete(self) -> None:
        server, env = build_session(access_level="read_write")
        email = seed_inbox_message(env)

        # 1. search
        search = tool_json(await server.call_tool("search_emails", {"query": "hi"}))
        assert search["total_count"] == 1
        assert env.gateway.list_calls  # reached the (mocked) Gmail API

        # 2. read the cached email by id
        read = tool_json(
            await server.call_tool("get_email", {"email_id": email.message_id.value})
        )
        assert read["subject"] == "Hello"

        # 3. forward
        fwd = tool_json(
            await server.call_tool(
                "forward_email",
                {"email_id": email.message_id.value, "to": "dest@corp.com"},
            )
        )
        assert "error" not in fwd
        assert len(env.gateway.sent) == 1

        # 4. archive
        arch = tool_json(
            await server.call_tool(
                "archive_email", {"email_id": email.message_id.value}
            )
        )
        assert arch == {"status": "archived"}
        assert ("m1", [], ["INBOX"]) in env.gateway.modify_calls

        # 5. delete (soft)
        deleted = tool_json(
            await server.call_tool("delete_email", {"email_id": email.message_id.value})
        )
        assert deleted == {"status": "deleted", "permanent": False}
        assert env.gateway.trashed == ["m1"]


class TestRailguardEnforcement:
    async def test_write_tools_absent_under_read_only(self) -> None:
        server, _ = build_session(access_level="read_only")

        names = {t.name for t in await server.list_tools()}

        assert names.isdisjoint(_WRITE_TOOLS)
        # read/intelligence/search tools remain available
        assert {"search_emails", "semantic_search", "summarize_email"} <= names

    async def test_denied_forward_surfaces_structured_error(self) -> None:
        server, env = build_session(
            access_level="read_write", allowed_recipients=["@corp.com"]
        )
        email = seed_inbox_message(env)

        result = tool_json(
            await server.call_tool(
                "forward_email",
                {"email_id": email.message_id.value, "to": "x@evil.com"},
            )
        )

        assert result["error"]["type"] == "permission_denied"
        assert "not allowed" in result["error"]["message"]
        assert env.gateway.sent == []  # nothing was sent
