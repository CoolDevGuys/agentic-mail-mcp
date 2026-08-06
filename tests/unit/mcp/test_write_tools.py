from __future__ import annotations

from agentic_mail_mcp.Gmail.Domain.Events import (
    EmailArchived,
    EmailForwarded,
    EmailLabeled,
)
from agentic_mail_mcp.MCP.errors import NOT_FOUND, PERMISSION_DENIED
from agentic_mail_mcp.MCP.Tools.write_tools import build_write_tools

from .conftest import make_env


def _tool(uses, name):
    return next(t for t in build_write_tools(uses) if t.name == name)


class TestForwardEmailTool:
    async def test_forwards_and_reaches_gateway(self) -> None:
        env = make_env()
        email = env.add_email()
        tool = _tool(env.uses, "forward_email")

        result = await tool.handler(email_id=email.message_id.value, to="dest@corp.com")

        assert "error" not in result
        assert env.gateway.sent
        assert any(isinstance(e, EmailForwarded) for e in env.event_bus.published)

    async def test_blocked_recipient_maps_to_permission_error(self) -> None:
        env = make_env(allowed_recipients=["@corp.com"])
        email = env.add_email()
        tool = _tool(env.uses, "forward_email")

        result = await tool.handler(email_id=email.message_id.value, to="x@evil.com")

        assert result["error"]["type"] == PERMISSION_DENIED
        assert "not allowed" in result["error"]["message"]
        assert env.gateway.sent == []

    async def test_read_only_validator_denies(self) -> None:
        env = make_env(access_level="read_only")
        email = env.add_email()
        # Even if a caller reaches the write tool directly, the use case's
        # validator denies it and the tool returns a structured error.
        tool = _tool(env.uses, "forward_email")

        result = await tool.handler(email_id=email.message_id.value, to="a@b.com")

        assert result["error"]["type"] == PERMISSION_DENIED

    async def test_unknown_message_id_maps_to_not_found(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "forward_email")

        result = await tool.handler(email_id="unknown-message-id", to="a@b.com")

        assert result["error"]["type"] == NOT_FOUND
        assert env.gateway.sent == []


class TestArchiveEmailTool:
    async def test_archives_single_email(self) -> None:
        env = make_env()
        email = env.add_email()
        tool = _tool(env.uses, "archive_email")

        result = await tool.handler(email_id=email.message_id.value)

        assert result == {"status": "archived"}
        assert env.gateway.modify_calls == [("m1", [], ["INBOX"])]
        assert any(isinstance(e, EmailArchived) for e in env.event_bus.published)


class TestDeleteEmailTool:
    async def test_soft_delete_trashes(self) -> None:
        env = make_env()
        email = env.add_email()
        tool = _tool(env.uses, "delete_email")

        result = await tool.handler(email_id=email.message_id.value)

        assert result == {"status": "deleted", "permanent": False}
        assert env.gateway.trashed == ["m1"]


class TestDraftTools:
    async def test_create_then_send_draft(self) -> None:
        env = make_env()
        create = _tool(env.uses, "create_draft")
        send = _tool(env.uses, "send_draft")

        created = await create.handler(to="a@b.com", subject="Hi", body="Body")
        assert created["draft_id"] == "draft-1"
        assert env.gateway.drafts_created

        sent = await send.handler(draft_id="draft-1")
        assert "error" not in sent
        assert env.gateway.drafts_sent == ["draft-1"]


class TestAddLabelTool:
    async def test_adds_label_and_emits_event(self) -> None:
        env = make_env()
        email = env.add_email()
        tool = _tool(env.uses, "add_label")

        result = await tool.handler(email_id=email.message_id.value, label="Important")

        assert result == {"status": "labeled", "label": "Important"}
        assert env.gateway.modify_calls == [("m1", ["Important"], [])]
        events = [e for e in env.event_bus.published if isinstance(e, EmailLabeled)]
        assert events and events[0].label_name == "Important"
