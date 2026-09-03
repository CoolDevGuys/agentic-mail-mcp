from __future__ import annotations

import inspect
import logging

from agentic_mail_mcp.Bootstrap.DependencyContainer import Container
from agentic_mail_mcp.Bootstrap.Settings import MCPConfig, RailguardsConfig, Settings
from agentic_mail_mcp.MCP.Resources import ResourceContext
from agentic_mail_mcp.MCP.Server import (
    _safe_handler,
    create_server,
    register_tools,
    resolve_transport,
    run_server,
)
from agentic_mail_mcp.MCP.ToolRegistry import READ, ToolDefinition, ToolRegistry
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

from .conftest import make_env

_WRITE_TOOL_NAMES = {
    "forward_email",
    "archive_email",
    "delete_email",
    "create_draft",
    "send_draft",
    "add_label",
}


def _container(settings: Settings, uses: McpUseCases) -> Container:
    container = Container.with_defaults(settings)
    container.singleton(McpUseCases, uses)
    container.singleton(
        ResourceContext,
        ResourceContext(
            account_email="me@example.com",
            access_level=settings.railguards.access_level,
        ),
    )
    return container


class TestCreateServer:
    async def test_builds_from_container_with_all_tools_when_read_write(self) -> None:
        settings = Settings(railguards=RailguardsConfig(access_level="read_write"))
        container = _container(settings, make_env(access_level="read_write").uses)

        server = create_server(container)

        tools = await server.list_tools()
        names = {t.name for t in tools}
        assert _WRITE_TOOL_NAMES.issubset(names)
        assert len(tools) == 18

    async def test_write_tools_absent_when_read_only(self) -> None:
        settings = Settings(railguards=RailguardsConfig(access_level="read_only"))
        container = _container(settings, make_env(access_level="read_only").uses)

        server = create_server(container)

        names = {t.name for t in await server.list_tools()}
        assert names.isdisjoint(_WRITE_TOOL_NAMES)
        assert len(names) == 12

    async def test_registers_resources_and_prompts(self) -> None:
        settings = Settings(railguards=RailguardsConfig(access_level="read_only"))
        container = _container(settings, make_env(access_level="read_only").uses)

        server = create_server(container)

        resources = {str(r.uri) for r in await server.list_resources()}
        prompts = {p.name for p in await server.list_prompts()}
        assert resources == {"gmail://account", "gmail://watch", "search://index"}
        assert {"search_strategy", "email_management", "summarize_email"} <= prompts

    async def test_tool_is_callable_end_to_end(self) -> None:
        env = make_env(access_level="read_write")
        settings = Settings(railguards=RailguardsConfig(access_level="read_write"))
        server = create_server(use_cases=env.uses, settings=settings)

        result = await server.call_tool("list_labels", {})

        assert result is not None

    def test_integrates_bootstrap_lifespan(self) -> None:
        from agentic_mail_mcp.Bootstrap.Lifespan import lifespan

        server = create_server(settings=Settings(), name="T")
        assert server.settings.lifespan is lifespan

    async def test_lifespan_starts_and_stops_cleanly(self) -> None:
        server = create_server(settings=Settings(), name="T")
        # Entering runs startup; exiting runs shutdown — both without error.
        async with server.settings.lifespan(server) as state:
            assert "settings" in state

    def test_uses_server_name_from_settings(self) -> None:
        settings = Settings(mcp=MCPConfig(server_name="My-Agentic-Mail-MCP"))
        server = create_server(settings=settings)
        assert server.name == "My-Agentic-Mail-MCP"


class TestTransport:
    def test_default_transport_is_stdio(self) -> None:
        assert resolve_transport(Settings()) == "stdio"

    def test_http_transport_selected(self) -> None:
        settings = Settings(mcp=MCPConfig(transport="http"))
        assert resolve_transport(settings) == "streamable-http"

    def test_run_server_dispatches_to_configured_transport(self) -> None:
        calls: list[str] = []

        class FakeServer:
            def run(self, transport: str) -> None:
                calls.append(transport)

        run_server(FakeServer(), Settings(mcp=MCPConfig(transport="stdio")))
        assert calls == ["stdio"]


class TestErrorSurfacing:
    """Unexpected exceptions must not reach the transport as opaque errors:
    they come back as a structured internal_error carrying the real cause."""

    async def test_unexpected_exception_becomes_structured_error(
        self, caplog
    ) -> None:
        async def boom(query: str = "") -> dict:
            raise TypeError("'NoneType' object is not iterable")

        registry = ToolRegistry()
        registry.register(
            ToolDefinition(name="boom", description="d", category=READ, handler=boom)
        )
        captured: dict[str, object] = {}

        class FakeServer:
            def add_tool(self, handler, *, name, description) -> None:
                captured[name] = handler

        register_tools(FakeServer(), registry)

        with caplog.at_level(logging.ERROR):
            result = await captured["boom"]()

        assert result == {
            "error": {
                "type": "internal_error",
                "message": "TypeError: 'NoneType' object is not iterable",
            }
        }
        assert "Unhandled exception in MCP tool boom" in caplog.text
        assert "Traceback" in caplog.text

    async def test_successful_handler_is_untouched(self) -> None:
        async def ok(query: str = "") -> dict:
            return {"hits": [query]}

        registry = ToolRegistry()
        registry.register(
            ToolDefinition(name="ok", description="d", category=READ, handler=ok)
        )
        captured: dict[str, object] = {}

        class FakeServer:
            def add_tool(self, handler, *, name, description) -> None:
                captured[name] = handler

        register_tools(FakeServer(), registry)

        assert await captured["ok"](query="hi") == {"hits": ["hi"]}

    def test_handler_signature_and_coroutine_flags_are_preserved(self) -> None:
        async def handler(subject: str, page: int = 1) -> dict:
            return {}

        wrapped = _safe_handler(handler)

        assert list(inspect.signature(wrapped).parameters) == ["subject", "page"]
        assert inspect.iscoroutinefunction(wrapped)
