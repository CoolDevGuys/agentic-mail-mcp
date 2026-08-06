"""MCP tool registry with category grouping and access-level gating.

A ``ToolDefinition`` bundles an agent-facing name/description, a category, an
async handler, and a JSON-Schema input schema (derived from the handler
signature). ``ToolRegistry`` groups tools by category and enforces
defense-in-depth: when the railguard access level is ``read_only`` the entire
``write`` category is refused registration, so write tools are never exposed to
the agent — not merely denied at execution time by the RailguardValidator.
"""

from __future__ import annotations

import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from types import UnionType
from typing import Any, Union, get_args, get_origin, get_type_hints

from agentic_mail_mcp.Common.Railguards.config import READ_ONLY

READ = "read"
WRITE = "write"
INTELLIGENCE = "intelligence"
SEARCH = "search"
CATEGORIES = frozenset({READ, WRITE, INTELLIGENCE, SEARCH})

ToolHandler = Callable[..., Awaitable[Any]]

_JSON_TYPES: dict[type, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    list: "array",
    dict: "object",
}


def _json_type(annotation: Any) -> str:
    origin = get_origin(annotation)
    if origin in (Union, UnionType):
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if non_none:
            return _json_type(non_none[0])
    if origin in (list, tuple, set):
        return "array"
    if origin is dict:
        return "object"
    return _JSON_TYPES.get(annotation, "string")


def build_schema(handler: ToolHandler) -> dict[str, Any]:
    """Derive a JSON-Schema ``object`` from a handler's typed signature.

    Parameters without a default are required. Optional (``X | None``) and
    defaulted parameters are optional. A ``context``/``self`` parameter, if any,
    is skipped.
    """
    signature = inspect.signature(handler)
    try:
        hints = get_type_hints(handler)
    except (NameError, TypeError):  # pragma: no cover - exotic annotations
        hints = {}

    properties: dict[str, Any] = {}
    required: list[str] = []
    for name, param in signature.parameters.items():
        if name in ("self", "context") or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        annotation = hints.get(name, param.annotation)
        properties[name] = {"type": _json_type(annotation)}
        if param.default is inspect.Parameter.empty:
            required.append(name)

    schema: dict[str, Any] = {"type": "object", "properties": properties}
    if required:
        schema["required"] = required
    return schema


@dataclass(frozen=True)
class ToolDefinition:
    name: str
    description: str
    category: str
    handler: ToolHandler
    input_schema: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.category not in CATEGORIES:
            raise ValueError(
                f"category must be one of {sorted(CATEGORIES)}, got {self.category!r}"
            )
        if not self.input_schema:
            object.__setattr__(self, "input_schema", build_schema(self.handler))


class ToolRegistry:
    """Holds registered tools grouped by category, gating writes by access level."""

    def __init__(self, access_level: str = READ_ONLY) -> None:
        self._access_level = access_level
        self._tools: dict[str, ToolDefinition] = {}

    @property
    def is_read_only(self) -> bool:
        return self._access_level == READ_ONLY

    def register(self, definition: ToolDefinition) -> bool:
        """Register a tool. Returns False (and skips) a write tool under
        read-only access; raises on duplicate names."""
        if definition.category == WRITE and self.is_read_only:
            return False
        if definition.name in self._tools:
            raise ValueError(f"tool already registered: {definition.name!r}")
        self._tools[definition.name] = definition
        return True

    def get(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    def names(self) -> list[str]:
        return list(self._tools.keys())

    def by_category(self, category: str) -> list[ToolDefinition]:
        return [d for d in self._tools.values() if d.category == category]
