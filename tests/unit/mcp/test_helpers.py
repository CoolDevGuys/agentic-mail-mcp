from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from src.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from src.MCP.errors import (
    INTERNAL_ERROR,
    INVALID_INPUT,
    NOT_FOUND,
    PERMISSION_DENIED,
    error_result,
    is_error_result,
)
from src.MCP.serialization import to_jsonable


@dataclass(frozen=True)
class _Sample:
    name: str
    when: datetime
    tags: list[str]


class TestSerialization:
    def test_dataclass_datetime_and_nested(self) -> None:
        sample = _Sample(name="x", when=datetime(2026, 1, 2, tzinfo=UTC), tags=["a", "b"])
        result = to_jsonable([sample])
        assert result == [
            {"name": "x", "when": "2026-01-02T00:00:00+00:00", "tags": ["a", "b"]}
        ]

    def test_primitives_pass_through(self) -> None:
        assert to_jsonable({"n": 1, "ok": True, "x": None}) == {
            "n": 1,
            "ok": True,
            "x": None,
        }


class TestErrorMapping:
    def test_permission_denied(self) -> None:
        result = error_result(PermissionError("nope"))
        assert result == {"error": {"type": PERMISSION_DENIED, "message": "nope"}}
        assert is_error_result(result)

    def test_not_found(self) -> None:
        assert error_result(NotFoundError("gone"))["error"]["type"] == NOT_FOUND

    def test_validation(self) -> None:
        assert error_result(ValidationError("bad"))["error"]["type"] == INVALID_INPUT

    def test_unknown_maps_to_internal(self) -> None:
        assert error_result(RuntimeError("boom"))["error"]["type"] == INTERNAL_ERROR

    def test_is_error_result_false_for_success(self) -> None:
        assert is_error_result({"ok": True}) is False
