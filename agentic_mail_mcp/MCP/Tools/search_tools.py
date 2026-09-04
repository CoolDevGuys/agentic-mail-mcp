"""Search-category MCP tools wrapping the semantic search use case."""

from __future__ import annotations

from typing import Any

from agentic_mail_mcp.Common.Domain.Exceptions import PermissionError, ValidationError
from agentic_mail_mcp.MCP.errors import error_result
from agentic_mail_mcp.MCP.serialization import to_jsonable
from agentic_mail_mcp.MCP.ToolRegistry import SEARCH, ToolDefinition
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

_SEARCH_ERRORS = (ValidationError, PermissionError)


def build_semantic_search_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.semantic_search
    assert use_case is not None, "semantic_search use case is required for this tool"

    async def semantic_search(
        query: str, limit: int = 10, min_score: float = 0.0
    ) -> dict[str, Any]:
        try:
            results = use_case.execute(query, limit=limit, min_score=min_score)
            return {"results": to_jsonable(results)}
        except _SEARCH_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="semantic_search",
        description=(
            "Search emails by meaning using natural language. Returns matches "
            "ranked by similarity score. Each result's `message_id` is the "
            "Gmail message id (pass it to get_email); it is null when the "
            "matched email is not in the local cache, in which case use "
            "search_emails to locate it."
        ),
        category=SEARCH,
        handler=semantic_search,
    )


def build_search_tools(uses: McpUseCases) -> list[ToolDefinition]:
    # Registered only when a vector backend is wired (the `search` extra).
    if uses.semantic_search is None:
        return []
    return [build_semantic_search_tool(uses)]
