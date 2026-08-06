from __future__ import annotations

import json

import httpx
import pytest
import respx

from agentic_mail_mcp.Notification.Infrastructure.Redis.redis_notification_gateway import (
    RedisNotificationGateway,
)
from agentic_mail_mcp.Notification.Infrastructure.Webhook.webhook_notification_gateway import (
    WebhookNotificationGateway,
)

fakeredis = pytest.importorskip("fakeredis")

_URL = "https://hooks.example.com/notify"


class TestWebhookNotificationGateway:
    @respx.mock
    def test_send_returns_true_on_success(self) -> None:
        route = respx.post(_URL).mock(return_value=httpx.Response(200))
        gateway = WebhookNotificationGateway(_URL)
        assert gateway.send("Title", "Body", "push") is True
        assert route.called
        sent = json.loads(route.calls.last.request.content)
        assert sent["title"] == "Title"
        assert sent["channel"] == "push"

    @respx.mock
    def test_publish_returns_true_on_success(self) -> None:
        respx.post(_URL).mock(return_value=httpx.Response(204))
        gateway = WebhookNotificationGateway(_URL)
        assert gateway.publish("email_added", {"id": "1"}) is True

    @respx.mock
    def test_returns_false_on_error_status(self) -> None:
        respx.post(_URL).mock(return_value=httpx.Response(500))
        gateway = WebhookNotificationGateway(_URL)
        assert gateway.send("t", "b", "push") is False

    @respx.mock
    def test_returns_false_when_unreachable(self) -> None:
        respx.post(_URL).mock(side_effect=httpx.ConnectError("boom"))
        gateway = WebhookNotificationGateway(_URL)
        assert gateway.publish("x", {}) is False


class TestRedisNotificationGateway:
    def test_publish_delivers_to_subscriber(self) -> None:
        client = fakeredis.FakeStrictRedis()
        pubsub = client.pubsub()
        pubsub.subscribe("agentic-mail-mcp:email_added")
        # Drain the subscribe confirmation message.
        pubsub.get_message(timeout=1)

        gateway = RedisNotificationGateway(client)
        assert gateway.publish("email_added", {"id": "1"}) is True

        message = pubsub.get_message(timeout=1)
        assert message is not None
        payload = json.loads(message["data"])
        assert payload["event_type"] == "email_added"

    def test_send_returns_true(self) -> None:
        gateway = RedisNotificationGateway(fakeredis.FakeStrictRedis())
        assert gateway.send("Title", "Body", "push") is True

    def test_publish_failure_returns_false(self) -> None:
        class BrokenRedis:
            def publish(self, *args, **kwargs):
                raise ConnectionError("down")

        gateway = RedisNotificationGateway(BrokenRedis())
        assert gateway.publish("x", {}) is False
