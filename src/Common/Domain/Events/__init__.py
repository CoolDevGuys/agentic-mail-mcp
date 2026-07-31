from datetime import UTC, datetime
from typing import Protocol
from uuid import UUID, uuid4

from ..ValueObjects.uuid_id import UUIDId


class DomainEvent:
    """Base class for domain events."""

    def __init__(
        self,
        aggregate_id: UUIDId,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        self.event_id = event_id or uuid4()
        self.occurred_at = occurred_at or datetime.now(UTC)
        self.aggregate_id = aggregate_id


class EventHandler(Protocol):
    """Protocol for domain event handlers."""

    def __call__(self, event: DomainEvent) -> None: ...


class EventBus(Protocol):
    """Protocol for publishing and subscribing to domain events."""

    def publish(self, event: DomainEvent) -> None: ...

    def subscribe(
        self, event_type: type[DomainEvent], handler: EventHandler
    ) -> None: ...

    def publish_all(self, events: list[DomainEvent]) -> None: ...


class InMemoryEventBus:
    """Synchronous, in-memory event bus implementation."""

    def __init__(self) -> None:
        self._subscribers: dict[type[DomainEvent], list[EventHandler]] = {}
        self._published: list[DomainEvent] = []

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(handler)

    def publish(self, event: DomainEvent) -> None:
        self._published.append(event)
        self._dispatch(event)

    def publish_all(self, events: list[DomainEvent]) -> None:
        for event in events:
            self.publish(event)

    def _dispatch(self, event: DomainEvent) -> None:
        event_type = type(event)
        for handler in self._subscribers.get(event_type, []):
            handler(event)

    @property
    def published(self) -> list[DomainEvent]:
        return list(self._published)
