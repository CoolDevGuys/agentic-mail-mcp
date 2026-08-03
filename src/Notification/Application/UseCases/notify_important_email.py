from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Common.Domain.Exceptions import DomainError
from src.Notification.Domain.Events.important_email_detected import (
    ImportantEmailDetected,
)
from src.Notification.Domain.Gateway.notification_gateway import NotificationGateway


class NotifyImportantEmailUseCase:
    """Subscribe to ImportantEmailDetected and dispatch a notification."""

    def __init__(
        self,
        gateway: NotificationGateway,
        *,
        channel: str = "default",
    ) -> None:
        self._gateway = gateway
        self._channel = channel

    def register(self, event_bus: EventBus) -> None:
        event_bus.subscribe(ImportantEmailDetected, self.handle)

    def handle(self, event: ImportantEmailDetected) -> None:
        title = f"Important email from {event.from_address}"
        body = f"{event.subject} (priority {event.priority})"
        delivered = self._gateway.send(title, body, self._channel)
        if not delivered:
            raise DomainError(
                f"Failed to deliver important-email notification for {event.email_id}"
            )
