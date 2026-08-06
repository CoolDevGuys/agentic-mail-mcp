"""MCP server bootstrap.

``create_server`` assembles a runnable MCP server from the DI container (or from
explicitly supplied pieces, which is how tests drive it): it builds the tool
registry — gating write tools by the railguard access level — and registers the
tools, resources, and prompts. ``run_server`` starts it on the configured
transport (stdio by default, streamable HTTP when selected).

All ``mcp``-library specifics live here; tools, the registry, resources, and
prompts are library-agnostic and unit-testable on their own.
"""

from __future__ import annotations

import inspect
import logging

from mcp.server import MCPServer

from agentic_mail_mcp.Bootstrap.DependencyContainer import Container
from agentic_mail_mcp.Bootstrap.Lifespan import lifespan
from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.MCP.Prompts import PromptDefinition, build_prompts
from agentic_mail_mcp.MCP.Resources import (
    ResourceContext,
    ResourceDefinition,
    build_resources,
)
from agentic_mail_mcp.MCP.ToolRegistry import ToolRegistry
from agentic_mail_mcp.MCP.Tools.builder import build_registry
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

_HTTP_TRANSPORTS = {"http", "streamable-http", "streamable_http"}

_logger = logging.getLogger(__name__)


def create_server(
    container: Container | None = None,
    *,
    use_cases: McpUseCases | None = None,
    settings: Settings | None = None,
    resources: ResourceContext | None = None,
    name: str | None = None,
) -> MCPServer:
    """Build the MCP server.

    Resolution order for each dependency: an explicit argument, then the
    container's registered singletons, then a sensible default. Write tools are
    only registered when ``settings.railguards.access_level`` is ``read_write``.
    """
    if settings is None and container is not None:
        settings = container.get(Settings)
    if settings is None:
        settings = Settings.from_env()

    if use_cases is None and container is not None:
        use_cases = container.get(McpUseCases)
    if resources is None and container is not None:
        resources = container.get(ResourceContext)

    server: MCPServer = MCPServer(
        name or settings.mcp.server_name,
        lifespan=lifespan,
    )

    if use_cases is not None:
        registry = build_registry(use_cases, settings.railguards.access_level)
        register_tools(server, registry)
    else:
        # No use-case bundle was supplied or registered on the container, so no
        # tools are exposed. This is a misconfigured composition root, not a
        # normal state — surface it rather than starting a silently empty server.
        _logger.warning(
            "MCP server built without an McpUseCases bundle; no tools registered. "
            "Register McpUseCases on the container to expose the Gmail tools."
        )

    if resources is not None:
        register_resources(server, resources)

    register_prompts(server)
    return server


def register_tools(server: MCPServer, registry: ToolRegistry) -> None:
    for definition in registry.definitions():
        server.add_tool(
            definition.handler,
            name=definition.name,
            description=definition.description,
        )


def _make_reader(resource: ResourceDefinition):
    # A zero-parameter reader: the server treats any handler parameter as a URI
    # template variable, so the resource is captured by closure instead.
    def _reader() -> object:
        return resource.read()

    return _reader


def register_resources(server: MCPServer, context: ResourceContext) -> None:
    for resource in build_resources(context):
        server.resource(
            resource.uri,
            name=resource.name,
            description=resource.description,
            mime_type=resource.mime_type,
        )(_make_reader(resource))


def _make_renderer(prompt: PromptDefinition):
    def _renderer(**kwargs: str) -> str:
        return prompt.render(**kwargs)

    # Expose the prompt's declared arguments as the handler's signature and
    # annotations so the server advertises them (and validates them) instead of
    # a lone ``kwargs``. The body still collects them via ``**kwargs``.
    params = [
        inspect.Parameter(arg, inspect.Parameter.KEYWORD_ONLY, annotation=str)
        for arg in prompt.arguments
    ]
    _renderer.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
    _renderer.__annotations__ = {arg: str for arg in prompt.arguments} | {"return": str}
    return _renderer


def register_prompts(server: MCPServer) -> None:
    for prompt in build_prompts():
        server.prompt(name=prompt.name, description=prompt.description)(
            _make_renderer(prompt)
        )


def resolve_transport(settings: Settings) -> str:
    transport = settings.mcp.transport.lower()
    if transport in _HTTP_TRANSPORTS:
        return "streamable-http"
    return "stdio"


def run_server(server: MCPServer, settings: Settings) -> None:
    """Run the server on the configured transport (blocking)."""
    if resolve_transport(settings) == "streamable-http":
        server.run("streamable-http", host=settings.mcp.host, port=settings.mcp.port)
    else:
        server.run("stdio")
