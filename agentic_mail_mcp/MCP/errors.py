"""Domain-error to structured-tool-error mapping.

Every MCP tool maps known domain failures to a structured error payload rather
than propagating an unhandled exception. This keeps the agent-facing surface
predictable: a railguard denial, a missing entity, or invalid input all come
back as ``{"error": {...}}`` with a stable ``type`` field.
"""

from __future__ import annotations

from typing import Any

from agentic_mail_mcp.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)

PERMISSION_DENIED = "permission_denied"
NOT_FOUND = "not_found"
INVALID_INPUT = "invalid_input"
INTERNAL_ERROR = "internal_error"

_ERROR_TYPES: tuple[tuple[type[Exception], str], ...] = (
    # PermissionError first: it is the railguard denial and the most specific.
    (PermissionError, PERMISSION_DENIED),
    (NotFoundError, NOT_FOUND),
    (ValidationError, INVALID_INPUT),
)


def error_type_for(exc: Exception) -> str:
    for exc_type, name in _ERROR_TYPES:
        if isinstance(exc, exc_type):
            return name
    return INTERNAL_ERROR


def error_result(exc: Exception) -> dict[str, Any]:
    """Build a structured tool-error payload from a domain exception."""
    return {"error": {"type": error_type_for(exc), "message": str(exc)}}


def is_error_result(result: Any) -> bool:
    return isinstance(result, dict) and "error" in result
