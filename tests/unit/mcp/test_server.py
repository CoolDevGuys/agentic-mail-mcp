from __future__ import annotations

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import MCPConfig, RailguardsConfig, Settings
from src.MCP.Resources import ResourceContext
from src.MCP.Server import create_server, resolve_transport, run_server
from src.MCP.Tools.use_cases import McpUseCases

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
        ResourceContext(account_email="me@example.com", access_level=settings.railguards.access_level),
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
        assert prompts == {"search_strategy", "email_management"}

    async def test_tool_is_callable_end_to_end(self) -> None:
        env = make_env(access_level="read_write")
        settings = Settings(railguards=RailguardsConfig(access_level="read_write"))
        server = create_server(use_cases=env.uses, settings=settings)

        result = await server.call_tool("list_labels", {})

        assert result is not None

    def test_integrates_bootstrap_lifespan(self) -> None:
        from src.Bootstrap.Lifespan import lifespan

        server = create_server(settings=Settings(), name="T")
        assert server.settings.lifespan is lifespan

    async def test_lifespan_starts_and_stops_cleanly(self) -> None:
        server = create_server(settings=Settings(), name="T")
        # Entering runs startup; exiting runs shutdown — both without error.
        async with server.settings.lifespan(server) as state:
            assert "settings" in state

    def test_uses_server_name_from_settings(self) -> None:
        settings = Settings(mcp=MCPConfig(server_name="My-Gmail-MCP"))
        server = create_server(settings=settings)
        assert server.name == "My-Gmail-MCP"


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
