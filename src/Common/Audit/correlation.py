"""Ambient correlation id for tying a write operation to its audit record."""

from __future__ import annotations

import uuid
from contextvars import ContextVar

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str) -> None:
    _correlation_id.set(value)


def get_correlation_id() -> str:
    """Return the current correlation id, generating and storing one if unset."""
    value = _correlation_id.get()
    if value is None:
        value = str(uuid.uuid4())
        _correlation_id.set(value)
    return value


def reset_correlation_id() -> None:
    _correlation_id.set(None)
