from __future__ import annotations

from typing import Any

from agentic_mail_mcp.Common.Audit.audit_log import AuditLog, AuditLogRepository
from agentic_mail_mcp.Common.Audit.correlation import get_correlation_id
from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Common.Infrastructure.Clock import Clock, SystemClock
from agentic_mail_mcp.Common.Infrastructure.IdGenerator import (
    IdGenerator,
    UuidIdGenerator,
)
from agentic_mail_mcp.Gmail.Domain.Events import (
    EmailArchived,
    EmailDeleted,
    EmailForwarded,
)


class AuditLogHandler:
    """Persists an audit entry for every write domain event.

    Subscribes to the Gmail write events; the correlation id is taken from the
    ambient context so an entry ties back to the operation that produced it.
    """

    def __init__(
        self,
        repository: AuditLogRepository,
        *,
        clock: Clock | None = None,
        id_generator: IdGenerator | None = None,
    ) -> None:
        self._repository = repository
        self._clock = clock or SystemClock()
        self._id_generator = id_generator or UuidIdGenerator()

    def register(self, event_bus: EventBus) -> None:
        event_bus.subscribe(EmailForwarded, self.on_forwarded)
        event_bus.subscribe(EmailArchived, self.on_archived)
        event_bus.subscribe(EmailDeleted, self.on_deleted)

    def on_forwarded(self, event: EmailForwarded) -> None:
        self._record("forward", event.email_id, {"forwarded_to": event.forwarded_to})

    def on_archived(self, event: EmailArchived) -> None:
        self._record("archive", event.email_id, {})

    def on_deleted(self, event: EmailDeleted) -> None:
        self._record("delete", event.email_id, {})

    def _record(self, action: str, email_id: Any, details: dict[str, Any]) -> None:
        self._repository.save(
            AuditLog(
                id=self._id_generator.generate(),
                action=action,
                timestamp=self._clock.now(),
                correlation_id=get_correlation_id(),
                email_id=str(email_id),
                details=details,
            )
        )
