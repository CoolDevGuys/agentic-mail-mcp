from collections.abc import Callable

from agentic_mail_mcp.Common.Domain.Events import DomainEvent, InMemoryEventBus
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


class _TestEvent(DomainEvent):
    pass


class _OtherEvent(DomainEvent):
    def __init__(self, aggregate_id: UUIDId, data: str) -> None:
        super().__init__(aggregate_id)
        self.data = data


class TestDomainEvent:
    def test_has_event_id(self) -> None:
        event = _TestEvent(aggregate_id=UUIDId.generate())
        assert event.event_id is not None

    def test_has_occurred_at(self) -> None:
        event = _TestEvent(aggregate_id=UUIDId.generate())
        assert event.occurred_at is not None

    def test_has_aggregate_id(self) -> None:
        aid = UUIDId.generate()
        event = _TestEvent(aggregate_id=aid)
        assert event.aggregate_id == aid


class TestInMemoryEventBusSubscribeAndPublish:
    def test_handler_invoked_on_publish(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []
        bus.subscribe(_TestEvent, received.append)
        event = _TestEvent(aggregate_id=UUIDId.generate())
        bus.publish(event)
        assert received == [event]

    def test_multiple_handlers(self) -> None:
        bus = InMemoryEventBus()
        r1: list[DomainEvent] = []
        r2: list[DomainEvent] = []
        bus.subscribe(_TestEvent, r1.append)
        bus.subscribe(_TestEvent, r2.append)
        event = _TestEvent(aggregate_id=UUIDId.generate())
        bus.publish(event)
        assert r1 == [event]
        assert r2 == [event]

    def test_no_handler(self) -> None:
        bus = InMemoryEventBus()
        event = _TestEvent(aggregate_id=UUIDId.generate())
        bus.publish(event)
        assert bus.published == [event]

    def test_other_event_type_not_dispatched(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []
        bus.subscribe(_TestEvent, received.append)
        other = _OtherEvent(aggregate_id=UUIDId.generate(), data="x")
        bus.publish(other)
        assert received == []


class TestPublishAll:
    def test_dispatches_all_events(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []
        bus.subscribe(_TestEvent, received.append)
        events = [
            _TestEvent(aggregate_id=UUIDId.generate()),
            _TestEvent(aggregate_id=UUIDId.generate()),
        ]
        bus.publish_all(events)
        assert len(received) == 2
        assert bus.published == events


class TestEventOrdering:
    def test_handlers_receive_in_order(self) -> None:
        bus = InMemoryEventBus()
        order: list[int] = []

        def make_handler(n: int) -> Callable[[DomainEvent], None]:
            def handler(_: DomainEvent) -> None:
                order.append(n)

            return handler

        bus.subscribe(_TestEvent, make_handler(1))
        bus.subscribe(_TestEvent, make_handler(2))
        bus.publish(_TestEvent(aggregate_id=UUIDId.generate()))
        assert order == [1, 2]

    def test_events_published_in_sequence(self) -> None:
        bus = InMemoryEventBus()
        received: list[DomainEvent] = []
        bus.subscribe(_TestEvent, received.append)
        e1 = _TestEvent(aggregate_id=UUIDId.generate())
        e2 = _TestEvent(aggregate_id=UUIDId.generate())
        bus.publish(e1)
        bus.publish(e2)
        assert received == [e1, e2]
