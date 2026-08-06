from __future__ import annotations

import logging

from agentic_mail_mcp.Common.Domain.Events import EventBus
from agentic_mail_mcp.Notification.Domain.Events.inbox_changed import InboxChanged
from agentic_mail_mcp.Notification.Domain.Gateway.notification_gateway import (
    NotificationGateway,
)

logger = logging.getLogger(__name__)


class PublishInboxEventUseCase:
    """Subscribe to inbox-change events and publish them to external channels.

    Publish failures are logged rather than raised: this handler runs inside the
    synchronous event bus, so raising would abort the producer of the event.
    Publishing to external channels is a non-critical side channel.
    """

    def __init__(
        self,
        gateway: NotificationGateway,
        *,
        channels: list[str] | None = None,
    ) -> None:
        self._gateway = gateway
        self._channels = channels or ["default"]

    def register(self, event_bus: EventBus) -> None:
        event_bus.subscribe(InboxChanged, self.handle)

    def handle(self, event: InboxChanged) -> None:
        for channel in self._channels:
            payload = {
                "event_type": event.event_type,
                "email_id": str(event.email_id),
                "changed_at": event.changed_at.isoformat(),
                "channel": channel,
            }
            published = self._gateway.publish(event.event_type, payload)
            if not published:
                logger.warning(
                    "Failed to publish inbox event",
                    extra={
                        "event_type": event.event_type,
                        "email_id": str(event.email_id),
                        "channel": channel,
                    },
                )
