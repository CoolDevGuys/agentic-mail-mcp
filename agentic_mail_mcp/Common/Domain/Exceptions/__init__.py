from typing import Any


class DomainError(Exception):
    """Base exception for all domain-layer errors."""

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(self.message)


class ValidationError(DomainError):
    """Value object or entity validation failure."""


class NotFoundError(DomainError):
    """Entity not found by ID."""


class PermissionError(DomainError):
    """Railguard or authorization violation."""


class ConcurrencyError(DomainError):
    """Optimistic lock / concurrent modification conflict."""
