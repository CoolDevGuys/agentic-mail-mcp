from __future__ import annotations

import json
import logging
from typing import Any

logger = logging.getLogger(__name__)


class RedisNotificationGateway:
    """NotificationGateway backed by Redis pub/sub.

    Returns True when the message is published and False on any Redis error;
    it never raises.
    """

    def __init__(self, redis_client: Any, *, channel_prefix: str = "gmail-mcp") -> None:
        self._redis = redis_client
        self._prefix = channel_prefix

    def _publish(self, channel: str, message: dict[str, Any]) -> bool:
        topic = f"{self._prefix}:{channel}"
        try:
            self._redis.publish(topic, json.dumps(message))
        except Exception as exc:  # noqa: BLE001 - redis errors vary; any failure = no delivery
            logger.warning(
                "Redis publish failed", extra={"topic": topic, "error": str(exc)}
            )
            return False
        return True

    def send(self, title: str, body: str, channel: str) -> bool:
        return self._publish(
            channel, {"kind": "notification", "title": title, "body": body}
        )

    def publish(self, event_type: str, payload: dict[str, Any]) -> bool:
        return self._publish(
            event_type, {"kind": "event", "event_type": event_type, "payload": payload}
        )
