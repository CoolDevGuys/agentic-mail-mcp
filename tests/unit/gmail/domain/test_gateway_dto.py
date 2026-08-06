from __future__ import annotations

from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailAttachment,
    GmailHistory,
    GmailLabel,
    GmailListResponse,
    GmailMessage,
    GmailMessageHeader,
    ModifyResult,
    SentMessageResult,
    StopWatchResult,
    WatchResponse,
)


class TestGmailMessageHeader:
    def test_instantiation(self) -> None:
        header = GmailMessageHeader(
            id="msg_1",
            thread_id="thread_1",
            snippet="Hello world",
            subject="Test Subject",
            from_="sender@example.com",
            date="2024-01-15T10:30:00Z",
            labels=["INBOX", "Unread"],
        )

        assert header.id == "msg_1"
        assert header.thread_id == "thread_1"
        assert header.snippet == "Hello world"
        assert header.subject == "Test Subject"
        assert header.from_ == "sender@example.com"
        assert header.date == "2024-01-15T10:30:00Z"
        assert header.labels == ["INBOX", "Unread"]


class TestGmailMessage:
    def test_instantiation_with_attachments(self) -> None:
        attachment = GmailAttachment(
            id="att_1",
            file_name="document.pdf",
            mime_type="application/pdf",
            size_bytes=1024,
        )

        message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="Hello world",
            subject="Test",
            from_="sender@example.com",
            to="recipient@example.com",
            date="2024-01-15T10:30:00Z",
            labels=["INBOX"],
            body="Full body text",
            attachments=[attachment],
        )

        assert message.id == "msg_1"
        assert message.to == "recipient@example.com"
        assert message.body == "Full body text"
        assert len(message.attachments) == 1
        assert message.attachments[0].file_name == "document.pdf"

    def test_instantiation_without_attachments(self) -> None:
        message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="",
            from_="",
            to="",
            date="",
            labels=[],
            body="",
            attachments=[],
        )

        assert message.attachments == []


class TestGmailAttachment:
    def test_instantiation(self) -> None:
        att = GmailAttachment(
            id="att_1",
            file_name="image.png",
            mime_type="image/png",
            size_bytes=2048,
        )

        assert att.id == "att_1"
        assert att.file_name == "image.png"
        assert att.mime_type == "image/png"
        assert att.size_bytes == 2048


class TestGmailListResponse:
    def test_with_results(self) -> None:
        header = GmailMessageHeader(
            id="msg_1",
            thread_id="thread_1",
            snippet="snippet",
            subject="subject",
            from_="from@example.com",
            date="2024-01-01",
            labels=[],
        )

        response = GmailListResponse(
            messages=[header],
            next_page_token="next_token",
            result_size_estimate=100,
        )

        assert len(response.messages) == 1
        assert response.next_page_token == "next_token"
        assert response.result_size_estimate == 100

    def test_no_more_pages(self) -> None:
        response = GmailListResponse(
            messages=[],
            next_page_token=None,
            result_size_estimate=0,
        )

        assert response.messages == []
        assert response.next_page_token is None


class TestSentMessageResult:
    def test_instantiation(self) -> None:
        result = SentMessageResult(
            message_id="msg_sent_1",
            thread_id="thread_sent_1",
        )

        assert result.message_id == "msg_sent_1"
        assert result.thread_id == "thread_sent_1"


class TestModifyResult:
    def test_instantiation(self) -> None:
        result = ModifyResult(label_ids=["INBOX", "Important"])

        assert result.label_ids == ["INBOX", "Important"]


class TestWatchResponse:
    def test_instantiation(self) -> None:
        response = WatchResponse(expiration=1735689600)

        assert response.expiration == 1735689600


class TestStopWatchResult:
    def test_success(self) -> None:
        result = StopWatchResult(success=True)
        assert result.success is True

    def test_failure(self) -> None:
        result = StopWatchResult(success=False)
        assert result.success is False


class TestGmailLabel:
    def test_user_label(self) -> None:
        label = GmailLabel(
            id="Label_1",
            name="Work",
            type="user",
            color="#FF0000",
        )

        assert label.type == "user"
        assert label.color == "#FF0000"

    def test_system_label(self) -> None:
        label = GmailLabel(
            id="INBOX",
            name="INBOX",
            type="system",
            color=None,
        )

        assert label.type == "system"
        assert label.color is None


class TestGmailHistory:
    def test_instantiation(self) -> None:
        header = GmailMessageHeader(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="",
            from_="",
            date="",
            labels=[],
        )

        label = GmailLabel(id="Label_1", name="Work", type="user", color=None)

        history = GmailHistory(
            history_id="hist_1",
            messages=[header],
            labels=[label],
        )

        assert history.history_id == "hist_1"
        assert len(history.messages) == 1
        assert len(history.labels) == 1
