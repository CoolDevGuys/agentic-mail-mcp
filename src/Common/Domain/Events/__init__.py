from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from typing import Any, Protocol, TypeVar
from uuid import UUID, uuid4

from ..ValueObjects.uuid_id import UUIDId

E = TypeVar("E")


class DomainEvent:
    """Rich base class offering standard event metadata.

    Inheriting from ``DomainEvent`` is optional. The event bus is generic over
    concrete event types (see :class:`EventBus`), so plain ``@dataclass`` events
    publish just as well. Use this base when an event wants the standard
    ``event_id`` / ``occurred_at`` / ``aggregate_id`` metadata.
    """

    def __init__(
        self,
        aggregate_id: UUIDId,
        event_id: UUID | None = None,
        occurred_at: datetime | None = None,
    ) -> None:
        self.event_id = event_id or uuid4()
        self.occurred_at = occurred_at or datetime.now(UTC)
        self.aggregate_id = aggregate_id


EventHandler = Callable[[Any], None]
"""A callable invoked with a published event of the type it subscribed to."""


class EventBus(Protocol):
    """Generic, type-keyed publish/subscribe bus for domain events.

    Events are dispatched to handlers registered for their concrete type; the
    bus does not require events to share a common base class.
    """

    def publish(self, event: object) -> None: ...

    def subscribe(
        self, event_type: type[E], handler: Callable[[E], None]
    ) -> None: ...

    def publish_all(self, events: Iterable[object]) -> None: ...


class InMemoryEventBus:
    """Synchronous, in-memory event bus implementation."""

    def __init__(self) -> None:
        self._subscribers: dict[type, list[Callable[[Any], None]]] = {}
        self._published: list[object] = []

    def subscribe(
        self, event_type: type[E], handler: Callable[[E], None]
    ) -> None:
        self._subscribers.setdefault(event_type, []).append(handler)

    def publish(self, event: object) -> None:
        self._published.append(event)
        self._dispatch(event)

    def publish_all(self, events: Iterable[object]) -> None:
        for event in events:
            self.publish(event)

    def _dispatch(self, event: object) -> None:
        for handler in self._subscribers.get(type(event), []):
            handler(event)

    @property
    def published(self) -> list[object]:
        return list(self._published)
