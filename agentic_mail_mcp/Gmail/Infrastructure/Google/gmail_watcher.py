from __future__ import annotations

import base64
import json
from typing import Any

from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailGateway,
    StopWatchResult,
    WatchResponse,
)


class GmailWatcher:
    """Manages Gmail push notifications and parses webhook callbacks."""

    def __init__(
        self,
        gateway: GmailGateway,
        *,
        notification_url: str,
        webhook_token: str,
    ) -> None:
        self._gateway = gateway
        self._notification_url = notification_url
        self._webhook_token = webhook_token

    def start(self) -> WatchResponse:
        return self._gateway.watch(self._notification_url, self._webhook_token)

    def stop(self) -> StopWatchResult:
        return self._gateway.stop_watch()

    def parse_callback(self, body: dict[str, Any]) -> str:
        """Extract the history id from a Pub/Sub push notification body."""
        data = body.get("message", {}).get("data", "")
        padded = data + "=" * (-len(data) % 4)
        decoded = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return str(decoded["historyId"])
