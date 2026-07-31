
from src.MCP.Server import create_server
from src.MCP.ToolRegistry import ToolRegistry


class TestCreateServer:
    def test_creates_server_with_default_name(self):
        server = create_server()
        assert server is not None

    def test_creates_server_with_custom_name(self):
        server = create_server(name="Custom-MCP")
        assert server is not None


class TestToolRegistry:
    def test_register_and_get(self):
        registry = ToolRegistry()
        registry.register("test-tool", {"name": "test"})
        assert registry.get("test-tool") == {"name": "test"}

    def test_get_returns_none_for_unknown(self):
        registry = ToolRegistry()
        assert registry.get("nonexistent") is None

    def test_list_registered_tools(self):
        registry = ToolRegistry()
        registry.register("tool1", None)
        registry.register("tool2", None)
        assert sorted(registry.list()) == ["tool1", "tool2"]

    def test_list_empty(self):
        registry = ToolRegistry()
        assert registry.list() == []

    def test_overwrite_tool(self):
        registry = ToolRegistry()
        registry.register("tool", "v1")
        registry.register("tool", "v2")
        assert registry.get("tool") == "v2"
