"""Search-category MCP tools wrapping the semantic search use case."""

from __future__ import annotations

from src.Common.Domain.Exceptions import PermissionError, ValidationError
from src.MCP.errors import error_result
from src.MCP.serialization import to_jsonable
from src.MCP.ToolRegistry import SEARCH, ToolDefinition
from src.MCP.Tools.use_cases import McpUseCases

_SEARCH_ERRORS = (ValidationError, PermissionError)


def build_semantic_search_tool(uses: McpUseCases) -> ToolDefinition:
    async def semantic_search(
        query: str, limit: int = 10, min_score: float = 0.0
    ) -> dict:
        try:
            results = uses.semantic_search.execute(query, limit=limit, min_score=min_score)
            return {"results": to_jsonable(results)}
        except _SEARCH_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="semantic_search",
        description=(
            "Search emails by meaning using natural language. Returns matches "
            "ranked by similarity score."
        ),
        category=SEARCH,
        handler=semantic_search,
    )


def build_search_tools(uses: McpUseCases) -> list[ToolDefinition]:
    return [build_semantic_search_tool(uses)]
