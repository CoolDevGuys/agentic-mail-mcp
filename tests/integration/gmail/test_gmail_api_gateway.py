from __future__ import annotations

import base64

from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
from agentic_mail_mcp.Gmail.Domain.Events import EmailReceived, InboxSynchronized
from agentic_mail_mcp.Gmail.Infrastructure.Google.gmail_api_gateway import (
    GmailApiGateway,
)
from agentic_mail_mcp.Gmail.Infrastructure.Google.gmail_history_synchronizer import (
    GmailHistorySynchronizer,
)
from agentic_mail_mcp.Gmail.Infrastructure.Google.gmail_watcher import GmailWatcher
from tests.fakes.ports import InMemoryEmailRepository
from tests.integration.gmail.fake_gmail_service import (
    FakeGmailService,
    FakeHttpError,
)


def _no_sleep(_: float) -> None:
    return None


def _full_message(msg_id: str = "m1") -> dict:
    return {
        "id": msg_id,
        "threadId": "t1",
        "snippet": "snip",
        "labelIds": ["INBOX", "UNREAD"],
        "payload": {
            "headers": [
                {"name": "Subject", "value": "Hello"},
                {"name": "From", "value": "sender@example.com"},
                {"name": "To", "value": "r@example.com"},
                {"name": "Date", "value": "2026-01-01"},
            ],
            "body": {"data": base64.urlsafe_b64encode(b"Body text").decode()},
        },
    }


def _gateway(service: FakeGmailService) -> GmailApiGateway:
    return GmailApiGateway(service, sleep=_no_sleep)


class TestGmailApiGateway:
    def test_list_messages_maps_response(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "messages.list",
            {
                "messages": [{"id": "m1", "threadId": "t1"}],
                "nextPageToken": "next",
                "resultSizeEstimate": 1,
            },
        )
        service.set_result(
            "messages.get",
            {
                "id": "m1",
                "threadId": "t1",
                "snippet": "snip",
                "labelIds": ["INBOX"],
                "payload": {
                    "headers": [
                        {"name": "Subject", "value": "Hello"},
                        {"name": "From", "value": "a@b.com"},
                        {"name": "Date", "value": "2026-01-01"},
                    ]
                },
            },
        )
        result = _gateway(service).list_messages("is:unread", None, 10)
        assert result.next_page_token == "next"
        assert result.result_size_estimate == 1
        assert result.messages[0].id == "m1"
        assert result.messages[0].subject == "Hello"
        assert result.messages[0].from_ == "a@b.com"

    def test_get_message_parses_full(self) -> None:
        service = FakeGmailService()
        service.set_result("messages.get", _full_message())
        message = _gateway(service).get_message("m1", "full")
        assert message is not None
        assert message.subject == "Hello"
        assert message.from_ == "sender@example.com"
        assert message.body == "Body text"

    def test_get_message_returns_none_on_404(self) -> None:
        service = FakeGmailService()
        service.set_outcomes("messages.get", [FakeHttpError(404)])
        assert _gateway(service).get_message("missing", "full") is None

    def test_transient_error_is_retried(self) -> None:
        service = FakeGmailService()
        service.set_outcomes("messages.get", [FakeHttpError(503), _full_message("m2")])
        message = _gateway(service).get_message("m2", "full")
        assert message is not None
        assert service.executed.count("messages.get") == 2

    def test_send_message(self) -> None:
        service = FakeGmailService()
        service.set_result("messages.send", {"id": "sent1", "threadId": "t9"})
        result = _gateway(service).send_message("cmF3")
        assert result.message_id == "sent1"
        assert result.thread_id == "t9"

    def test_modify_message(self) -> None:
        service = FakeGmailService()
        service.set_result("messages.modify", {"labelIds": ["INBOX"]})
        result = _gateway(service).modify_message("m1", ["INBOX"], ["UNREAD"])
        assert result.label_ids == ["INBOX"]

    def test_trash_and_delete_execute(self) -> None:
        service = FakeGmailService()
        gateway = _gateway(service)
        gateway.trash_message("m1")
        gateway.delete_message("m1")
        assert "messages.trash" in service.executed
        assert "messages.delete" in service.executed

    def test_list_labels(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "labels.list",
            {"labels": [{"id": "INBOX", "name": "INBOX", "type": "system"}]},
        )
        labels = _gateway(service).list_labels()
        assert labels[0].name == "INBOX"
        assert labels[0].type == "system"

    def test_download_attachment_decodes(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "messages.attachments.get",
            {"data": base64.urlsafe_b64encode(b"file-bytes").decode()},
        )
        data = _gateway(service).download_attachment("m1", "att1")
        assert data == b"file-bytes"

    def test_create_draft_maps_response(self) -> None:
        service = FakeGmailService()
        service.set_result("drafts.create", {"id": "draft1", "message": {"id": "msg1"}})
        result = _gateway(service).create_draft("cmF3")
        assert result.draft_id == "draft1"
        assert result.message_id == "msg1"
        assert service.calls[0][0] == "drafts.create"

    def test_send_draft_maps_response(self) -> None:
        service = FakeGmailService()
        service.set_result("drafts.send", {"id": "sent1", "threadId": "t1"})
        result = _gateway(service).send_draft("draft1")
        assert result.message_id == "sent1"
        assert result.thread_id == "t1"

    def test_delete_draft_executes(self) -> None:
        service = FakeGmailService()
        _gateway(service).delete_draft("draft1")
        assert "drafts.delete" in service.executed

    def test_get_history_maps_added_messages(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "history.list",
            {
                "historyId": "999",
                "history": [
                    {"messagesAdded": [{"message": {"id": "m1", "threadId": "t1"}}]}
                ],
            },
        )
        history = _gateway(service).get_history("100", "100")
        assert history.history_id == "999"
        assert history.messages[0].id == "m1"


class TestGmailWatcher:
    def test_parse_callback_extracts_history_id(self) -> None:
        import base64 as b64
        import json

        service = FakeGmailService()
        watcher = GmailWatcher(
            _gateway(service), notification_url="topic", webhook_token="tok"
        )
        data = b64.urlsafe_b64encode(
            json.dumps({"emailAddress": "u@x.com", "historyId": "42"}).encode()
        ).decode()
        assert watcher.parse_callback({"message": {"data": data}}) == "42"

    def test_start_and_stop_delegate(self) -> None:
        service = FakeGmailService()
        service.set_result("watch", {"expiration": 123})
        watcher = GmailWatcher(
            _gateway(service), notification_url="topic", webhook_token="tok"
        )
        assert watcher.start().expiration == 123
        assert watcher.stop().success is True


class TestGmailHistorySynchronizer:
    def test_applies_new_messages_and_emits_events(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "history.list",
            {
                "historyId": "999",
                "history": [
                    {"messagesAdded": [{"message": {"id": "m1", "threadId": "t1"}}]}
                ],
            },
        )
        service.set_result("messages.get", _full_message("m1"))
        repo = InMemoryEmailRepository()
        bus = InMemoryEventBus()
        sync = GmailHistorySynchronizer(_gateway(service), repo, bus)

        count = sync.synchronize("100")
        assert count == 1
        assert repo.find_by_gmail_message_id("m1") is not None
        assert any(isinstance(e, EmailReceived) for e in bus.published)
        assert any(isinstance(e, InboxSynchronized) for e in bus.published)

    def test_synchronize_is_idempotent(self) -> None:
        service = FakeGmailService()
        service.set_result(
            "history.list",
            {
                "historyId": "999",
                "history": [
                    {"messagesAdded": [{"message": {"id": "m1", "threadId": "t1"}}]}
                ],
            },
        )
        service.set_result("messages.get", _full_message("m1"))
        repo = InMemoryEmailRepository()
        bus = InMemoryEventBus()
        sync = GmailHistorySynchronizer(_gateway(service), repo, bus)

        sync.synchronize("100")
        second = sync.synchronize("100")
        assert second == 0
