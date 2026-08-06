from __future__ import annotations

import logging

from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Notification.Domain.Events.important_email_detected import (
    ImportantEmailDetected,
)
from agentic_mail_mcp.Notification.Domain.Gateway.notification_gateway import (
    NotificationGateway,
)

logger = logging.getLogger(__name__)


class NotifyImportantEmailUseCase:
    """Subscribe to ImportantEmailDetected and dispatch a notification.

    Delivery failures are logged rather than raised: this handler runs inside
    the synchronous event bus, so raising would abort the producer of the event
    and starve other subscribers. Notification delivery is a non-critical side
    channel and must not fail the originating operation.
    """

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
            logger.warning(
                "Failed to deliver important-email notification",
                extra={"email_id": str(event.email_id), "channel": self._channel},
            )
