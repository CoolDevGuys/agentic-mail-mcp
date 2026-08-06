from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Protocol, runtime_checkable

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class AuditLog:
    """A record of a single write operation."""

    id: UUIDId
    action: str
    timestamp: datetime
    correlation_id: str
    email_id: str | None = None
    details: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class AuditLogRepository(Protocol):
    def save(self, entry: AuditLog) -> None: ...

    def list_all(self) -> list[AuditLog]: ...
