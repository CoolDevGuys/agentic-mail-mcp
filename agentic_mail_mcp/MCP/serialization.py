"""JSON-serialization helpers for MCP tool and resource results.

Application-layer DTOs are frozen dataclasses; MCP results must be plain
JSON-compatible values. ``to_jsonable`` converts dataclasses, datetimes,
UUID-like value objects, and nested containers into that shape.
"""

from __future__ import annotations

import dataclasses
from datetime import date, datetime
from typing import Any


def to_jsonable(value: Any) -> Any:
    """Recursively convert ``value`` into JSON-compatible primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {
            f.name: to_jsonable(getattr(value, f.name))
            for f in dataclasses.fields(value)
        }
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_jsonable(v) for v in value]
    return str(value)
