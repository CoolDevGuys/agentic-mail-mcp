"""Assemble the full tool set into a ToolRegistry, applying access-level gating."""

from __future__ import annotations

from agentic_mail_mcp.Common.Railguards.config import READ_ONLY
from agentic_mail_mcp.MCP.ToolRegistry import ToolRegistry
from agentic_mail_mcp.MCP.Tools.intelligence_tools import build_intelligence_tools
from agentic_mail_mcp.MCP.Tools.read_tools import build_read_tools
from agentic_mail_mcp.MCP.Tools.search_tools import build_search_tools
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases
from agentic_mail_mcp.MCP.Tools.write_tools import build_write_tools


def build_registry(uses: McpUseCases, access_level: str = READ_ONLY) -> ToolRegistry:
    """Build a ToolRegistry from the use-case bundle.

    Read, intelligence, and search tools are always registered. Write tools are
    registered only when ``access_level`` is ``read_write``; under ``read_only``
    the registry refuses them so they never reach the agent.
    """
    registry = ToolRegistry(access_level=access_level)
    for definition in build_read_tools(uses):
        registry.register(definition)
    for definition in build_write_tools(uses):
        registry.register(definition)
    for definition in build_intelligence_tools(uses):
        registry.register(definition)
    for definition in build_search_tools(uses):
        registry.register(definition)
    return registry
