from __future__ import annotations

import pytest

from src.MCP.ToolRegistry import (
    CATEGORIES,
    INTELLIGENCE,
    READ,
    SEARCH,
    WRITE,
    ToolDefinition,
    ToolRegistry,
    build_schema,
)
from src.MCP.Tools.builder import build_registry

from .conftest import make_env

_WRITE_TOOL_NAMES = {
    "forward_email",
    "archive_email",
    "delete_email",
    "create_draft",
    "send_draft",
    "add_label",
}


async def _noop(email_id: str, limit: int = 5) -> dict:
    return {}


class TestBuildSchema:
    def test_derives_required_and_optional(self) -> None:
        schema = build_schema(_noop)
        assert schema["type"] == "object"
        assert schema["properties"]["email_id"] == {"type": "string"}
        assert schema["properties"]["limit"] == {"type": "integer"}
        assert schema["required"] == ["email_id"]

    def test_optional_union_has_no_required(self) -> None:
        async def handler(name: str | None = None) -> dict:
            return {}

        schema = build_schema(handler)
        assert schema["properties"]["name"] == {"type": "string"}
        assert "required" not in schema


class TestToolDefinition:
    def test_schema_autoderived_when_absent(self) -> None:
        definition = ToolDefinition("t", "desc", READ, _noop)
        assert definition.input_schema["properties"]["email_id"]["type"] == "string"

    def test_invalid_category_rejected(self) -> None:
        with pytest.raises(ValueError):
            ToolDefinition("t", "desc", "bogus", _noop)


class TestToolRegistryGating:
    def test_write_tools_absent_when_read_only(self) -> None:
        registry = build_registry(make_env().uses, "read_only")
        names = set(registry.names())
        assert names.isdisjoint(_WRITE_TOOL_NAMES)
        assert registry.by_category(WRITE) == []

    def test_read_intelligence_search_present_when_read_only(self) -> None:
        registry = build_registry(make_env().uses, "read_only")
        assert registry.by_category(READ)
        assert registry.by_category(INTELLIGENCE)
        assert registry.by_category(SEARCH)

    def test_all_tools_present_when_read_write(self) -> None:
        registry = build_registry(make_env().uses, "read_write")
        names = set(registry.names())
        assert _WRITE_TOOL_NAMES.issubset(names)
        assert {"search_emails", "get_email", "semantic_search"}.issubset(names)

    def test_every_tool_has_valid_schema_and_category(self) -> None:
        registry = build_registry(make_env().uses, "read_write")
        for definition in registry.definitions():
            assert definition.category in CATEGORIES
            assert definition.description
            assert definition.input_schema["type"] == "object"

    def test_register_returns_false_for_gated_write(self) -> None:
        registry = ToolRegistry(access_level="read_only")
        write_def = ToolDefinition("w", "d", WRITE, _noop)
        assert registry.register(write_def) is False
        assert registry.get("w") is None

    def test_duplicate_registration_raises(self) -> None:
        registry = ToolRegistry(access_level="read_write")
        registry.register(ToolDefinition("dup", "d", READ, _noop))
        with pytest.raises(ValueError):
            registry.register(ToolDefinition("dup", "d", READ, _noop))
