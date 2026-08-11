from __future__ import annotations

from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailLabel,
    GmailListResponse,
    GmailMessage,
    GmailMessageHeader,
    GmailThread,
)
from agentic_mail_mcp.MCP.errors import INVALID_INPUT, NOT_FOUND
from agentic_mail_mcp.MCP.Tools.read_tools import build_read_tools

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

    async def test_malformed_date_maps_to_invalid_input(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "search_emails")

        result = await tool.handler(query="x", date_from="07/01/2026")

        assert result["error"]["type"] == INVALID_INPUT
        assert env.gateway.list_calls == []  # never reached the use case

    async def test_results_include_body_recipients_and_a_usable_id(self) -> None:
        env = make_env()
        env.gateway.list_response = GmailListResponse(
            messages=[
                GmailMessageHeader(
                    id="m1",
                    thread_id="t1",
                    snippet="hi",
                    subject="Hello",
                    from_="sender@example.com",
                    date="",
                    labels=["INBOX"],
                    to="me@example.com, cc@example.com",
                    body="Full email content",
                )
            ],
            next_page_token=None,
            result_size_estimate=1,
        )
        tool = _tool(env.uses, "search_emails")

        result = await tool.handler(query="hello")

        [email] = result["emails"]
        assert email["body"] == "Full email content"
        assert email["to_addresses"] == ["me@example.com", "cc@example.com"]
        # There is no internal cache UUID for a live result, so `id` falls
        # back to the Gmail message id instead of being blank — the same
        # value get_email actually accepts.
        assert email["id"] == "m1"
        assert email["message_id"] == "m1"


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


class TestGetThreadTool:
    async def test_returns_full_conversation_with_bodies(self) -> None:
        env = make_env()
        env.gateway.threads["t1"] = GmailThread(
            id="t1",
            snippet="snip",
            history_id="h1",
            messages=[
                GmailMessage(
                    id="m1",
                    thread_id="t1",
                    snippet="s1",
                    subject="Question",
                    from_="a@b.com",
                    to="me@example.com",
                    date="",
                    labels=["INBOX"],
                    body="Original message",
                    attachments=[],
                ),
                GmailMessage(
                    id="m2",
                    thread_id="t1",
                    snippet="s2",
                    subject="Re: Question",
                    from_="me@example.com",
                    to="a@b.com",
                    date="",
                    labels=["INBOX"],
                    body="My reply",
                    attachments=[],
                ),
            ],
        )
        tool = _tool(env.uses, "get_thread")

        result = await tool.handler(thread_id="t1")

        assert [e["body"] for e in result["emails"]] == [
            "Original message",
            "My reply",
        ]
        assert result["email_ids"] == ["m1", "m2"]

    async def test_missing_thread_maps_to_not_found(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "get_thread")

        result = await tool.handler(thread_id="missing")

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
