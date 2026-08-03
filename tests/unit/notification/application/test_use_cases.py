from __future__ import annotations

import logging
from contextlib import contextmanager

from src.Common.Domain.Events import InMemoryEventBus
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Notification.Application.UseCases.notify_important_email import (
    NotifyImportantEmailUseCase,
)
from src.Notification.Application.UseCases.publish_inbox_event import (
    PublishInboxEventUseCase,
)
from src.Notification.Domain.Events.important_email_detected import (
    ImportantEmailDetected,
)
from src.Notification.Domain.Events.inbox_changed import InboxChanged
from tests.fakes.ports import RecordingNotificationGateway


@contextmanager
def capture_logs(logger_name: str, level: int = logging.WARNING):
    """Attach a dedicated handler to a specific logger.

    Order-independent unlike caplog's root capture, which suite-wide logging
    reconfiguration can defeat.
    """
    records: list[logging.LogRecord] = []

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            records.append(record)

    logger = logging.getLogger(logger_name)
    handler = _Handler()
    handler.setLevel(level)
    previous_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(level)
    try:
        yield records
    finally:
        logger.removeHandler(handler)
        logger.setLevel(previous_level)


class TestNotifyImportantEmailUseCase:
    def test_dispatches_on_event(self) -> None:
        gateway = RecordingNotificationGateway()
        uc = NotifyImportantEmailUseCase(gateway, channel="push")
        bus = InMemoryEventBus()
        uc.register(bus)

        bus.publish(
            ImportantEmailDetected(
                email_id=UUIDId.generate(),
                from_address="boss@corp.com",
                subject="Urgent",
                priority=5,
            )
        )
        assert len(gateway.sent) == 1
        assert gateway.sent[0]["channel"] == "push"
        assert "boss@corp.com" in gateway.sent[0]["title"]
        assert "priority 5" in gateway.sent[0]["body"]

    def test_delivery_failure_is_logged_not_raised(self) -> None:
        gateway = RecordingNotificationGateway(send_result=False)
        uc = NotifyImportantEmailUseCase(gateway)
        bus = InMemoryEventBus()
        uc.register(bus)

        with capture_logs(
            "src.Notification.Application.UseCases.notify_important_email"
        ) as records:
            # Must not raise into the bus / producer.
            bus.publish(
                ImportantEmailDetected(
                    email_id=UUIDId.generate(),
                    from_address="x@y.com",
                    subject="s",
                    priority=3,
                )
            )

        assert len(gateway.sent) == 1
        assert any(
            "Failed to deliver important-email notification" in r.getMessage()
            for r in records
        )

    def test_failure_does_not_starve_other_subscribers(self) -> None:
        gateway = RecordingNotificationGateway(send_result=False)
        uc = NotifyImportantEmailUseCase(gateway)
        bus = InMemoryEventBus()
        uc.register(bus)

        other_calls: list[ImportantEmailDetected] = []
        bus.subscribe(ImportantEmailDetected, other_calls.append)

        bus.publish(
            ImportantEmailDetected(
                email_id=UUIDId.generate(),
                from_address="x@y.com",
                subject="s",
                priority=3,
            )
        )
        assert len(other_calls) == 1


class TestPublishInboxEventUseCase:
    def test_publishes_event(self) -> None:
        gateway = RecordingNotificationGateway()
        uc = PublishInboxEventUseCase(gateway)
        bus = InMemoryEventBus()
        uc.register(bus)

        eid = UUIDId.generate()
        bus.publish(InboxChanged(event_type="email_added", email_id=eid))

        assert len(gateway.published) == 1
        assert gateway.published[0]["event_type"] == "email_added"
        assert gateway.published[0]["payload"]["email_id"] == str(eid)

    def test_multi_channel_publishing(self) -> None:
        gateway = RecordingNotificationGateway()
        uc = PublishInboxEventUseCase(gateway, channels=["redis", "webhook"])
        bus = InMemoryEventBus()
        uc.register(bus)

        bus.publish(InboxChanged(event_type="email_removed", email_id=UUIDId.generate()))

        assert len(gateway.published) == 2
        channels = {p["payload"]["channel"] for p in gateway.published}
        assert channels == {"redis", "webhook"}

    def test_publish_failure_is_logged_not_raised(self) -> None:
        gateway = RecordingNotificationGateway(publish_result=False)
        uc = PublishInboxEventUseCase(gateway, channels=["redis"])
        bus = InMemoryEventBus()
        uc.register(bus)

        with capture_logs(
            "src.Notification.Application.UseCases.publish_inbox_event"
        ) as records:
            bus.publish(
                InboxChanged(event_type="email_added", email_id=UUIDId.generate())
            )

        assert len(gateway.published) == 1
        assert any(
            "Failed to publish inbox event" in r.getMessage() for r in records
        )
