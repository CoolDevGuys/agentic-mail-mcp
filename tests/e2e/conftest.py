"""Helpers for end-to-end MCP-session tests.

These tests drive the fully assembled MCP server through its protocol surface
(``call_tool`` / ``list_tools``) with the Gmail API mocked at the gateway seam,
exercising the same path an agent harness would.
"""

from __future__ import annotations

import json
from typing import Any

from agentic_mail_mcp.Bootstrap.Settings import RailguardsConfig, Settings
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailListResponse,
    GmailMessageHeader,
)
from agentic_mail_mcp.MCP.Server import create_server
from tests.unit.mcp.conftest import McpEnv, make_env


def build_session(
    *,
    access_level: str = "read_write",
    allowed_recipients: list[str] | None = None,
) -> tuple[Any, McpEnv]:
    """Assemble a real MCP server over an in-memory (mocked) Gmail backend."""
    env = make_env(access_level=access_level, allowed_recipients=allowed_recipients)
    settings = Settings(railguards=RailguardsConfig(access_level=access_level))
    server = create_server(use_cases=env.uses, settings=settings)
    return server, env


def seed_inbox_message(env: McpEnv, message_id: str = "m1"):
    """Add an email to the mocked mailbox and make it discoverable via search."""
    email = env.add_email(message_id=message_id)
    env.gateway.list_response = GmailListResponse(
        messages=[
            GmailMessageHeader(
                id=message_id,
                thread_id="t1",
                snippet="hi",
                subject="Hello",
                from_="sender@example.com",
                date="",
                labels=["INBOX"],
            )
        ],
        next_page_token=None,
        result_size_estimate=1,
    )
    return email


def tool_json(result: Any) -> dict:
    """Parse a CallToolResult's text content back into the tool's JSON payload."""
    assert result.content, "tool returned no content"
    return json.loads(result.content[0].text)
