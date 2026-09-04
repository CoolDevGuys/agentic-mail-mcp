"""Structured-output tests for the MCP tool surface.

Handlers must be annotated ``dict[str, Any]`` (not a bare ``dict``) so the MCP
SDK derives an output schema and the call result carries the payload as real
structured content — otherwise clients only see a JSON text block and must
parse it again (and some wrap it as ``{"result": "<string>"}``).
"""

from __future__ import annotations

from typing import Any

from mcp.server.mcpserver.utilities.func_metadata import func_metadata

from agentic_mail_mcp.MCP.Tools.builder import build_registry

from .conftest import make_env


def _definitions():
    env = make_env(access_level="read_write")
    return build_registry(env.uses, "read_write").definitions()


def test_registry_exposes_every_tool_category() -> None:
    names = {definition.name for definition in _definitions()}
    assert {
        "search_emails",
        "get_email",
        "get_thread",
        "list_unread",
        "list_labels",
        "semantic_search",
    } <= names


def test_every_tool_produces_unwrapped_structured_content() -> None:
    for definition in _definitions():
        metadata = func_metadata(definition.handler)
        assert metadata.output_schema is not None, (
            f"{definition.name}: SDK cannot derive a structured output schema"
        )
        assert metadata.wrap_output is False, (
            f"{definition.name}: output would be wrapped in {{'result': ...}}"
        )
        payload: dict[str, Any] = {"emails": [{"id": "m1"}], "page": 1}
        result = metadata.convert_result(dict(payload))
        assert result.structured_content == payload
