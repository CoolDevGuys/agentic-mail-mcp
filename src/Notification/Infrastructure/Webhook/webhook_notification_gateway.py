from __future__ import annotations

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)


class WebhookNotificationGateway:
    """NotificationGateway that POSTs payloads to a configured webhook URL.

    Returns True on a 2xx response and False on any error or unreachable
    endpoint; it never raises, so a downed webhook cannot break callers.
    """

    def __init__(
        self,
        url: str,
        *,
        client: httpx.Client | None = None,
        timeout: float = 5.0,
    ) -> None:
        self._url = url
        self._client = client or httpx.Client(timeout=timeout)

    def _post(self, body: dict[str, Any]) -> bool:
        try:
            response = self._client.post(self._url, json=body)
        except httpx.HTTPError as exc:
            logger.warning("Webhook POST failed", extra={"error": str(exc)})
            return False
        if response.is_success:
            return True
        logger.warning(
            "Webhook returned non-2xx", extra={"status": response.status_code}
        )
        return False

    def send(self, title: str, body: str, channel: str) -> bool:
        return self._post(
            {"kind": "notification", "title": title, "body": body, "channel": channel}
        )

    def publish(self, event_type: str, payload: dict[str, Any]) -> bool:
        return self._post(
            {"kind": "event", "event_type": event_type, "payload": payload}
        )
