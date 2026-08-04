from __future__ import annotations

from src.Gmail.Domain.Gateway.gmail_gateway import GmailLabel, GmailListResponse
from src.MCP.errors import INVALID_INPUT, NOT_FOUND
from src.MCP.Tools.read_tools import build_read_tools

from .conftest import make_env


def _tool(uses, name):
    return next(t for t in build_read_tools(uses) if t.name == name)


class TestSearchEmailsTool:
    async def test_wires_to_use_case_and_paginates(self) -> None:
        env = make_env()
        env.gateway.list_response = GmailListResponse(
            messages=[], next_page_token="next", result_size_estimate=0
        )
        tool = _tool(env.uses, "search_emails")

        result = await tool.handler(query="hello", page=2, page_size=10)

        assert result["page"] == 2
        assert result["page_size"] == 10
        assert result["next_page_token"] == "next"
        assert env.gateway.list_calls  # use case reached the gateway

    async def test_invalid_pagination_maps_to_error(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "search_emails")

        result = await tool.handler(query="x", page=0)

        assert result["error"]["type"] == INVALID_INPUT


class TestGetEmailTool:
    async def test_resolves_by_uuid(self) -> None:
        env = make_env()
        email = env.add_email()
        tool = _tool(env.uses, "get_email")

        result = await tool.handler(email_id=str(email.id))

        assert result["message_id"] == "m1"
        assert result["subject"] == "Hello"

    async def test_missing_email_maps_to_not_found(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "get_email")

        # A non-UUID id is treated as a Gmail message id and falls through to the
        # gateway, which has no such message.
        result = await tool.handler(email_id="unknown-gmail-id")

        assert result["error"]["type"] == NOT_FOUND


class TestListLabelsTool:
    async def test_returns_labels(self) -> None:
        env = make_env()
        env.gateway.labels = [
            GmailLabel(id="L1", name="Work", type="user", color="#fff"),
        ]
        tool = _tool(env.uses, "list_labels")

        result = await tool.handler(label_type="all")

        assert [label["name"] for label in result["labels"]] == ["Work"]


class TestListUnreadTool:
    async def test_returns_unread_emails(self) -> None:
        env = make_env()
        env.add_email(labels=["INBOX", "UNREAD"])
        tool = _tool(env.uses, "list_unread")

        result = await tool.handler(limit=10)

        assert len(result["emails"]) == 1
