from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Notification.Domain.Events.inbox_changed import InboxChanged
from src.Notification.Domain.Gateway.notification_gateway import NotificationGateway


class PublishInboxEventUseCase:
    """Subscribe to inbox-change events and publish them to external channels."""

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
            self._gateway.publish(event.event_type, payload)
