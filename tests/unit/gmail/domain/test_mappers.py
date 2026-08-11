from __future__ import annotations

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailMessage
from agentic_mail_mcp.Gmail.Domain.Mapper.email_mapper import EmailMapper
from agentic_mail_mcp.Gmail.Domain.Mapper.thread_mapper import ThreadMapper
from agentic_mail_mcp.Gmail.Domain.ValueObjects import (
    EmailAddress,
    GmailMessageId,
    ThreadId,
)


class TestEmailMapper:
    def test_to_domain_basic(self) -> None:
        gateway_message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="Hello world",
            subject="Test Subject",
            from_="sender@example.com",
            to="recipient@example.com",
            date="Mon, 15 Jan 2024 10:30:00 +0000",
            labels=["INBOX", "Unread"],
            body="Full body text",
            attachments=[],
        )

        email = EmailMapper.to_domain(gateway_message)

        assert isinstance(email.id, UUIDId)
        assert email.message_id == GmailMessageId("msg_1")
        assert email.thread_id == ThreadId("thread_1")
        assert email.snippet == "Hello world"
        assert email.subject == "Test Subject"
        assert email.from_address == EmailAddress("sender@example.com")
        assert email.to_addresses == [EmailAddress("recipient@example.com")]
        assert email.body == "Full body text"
        assert email.labels == frozenset({"INBOX", "Unread"})
        assert email.is_read is False

    def test_to_domain_parses_date(self) -> None:
        gateway_message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="",
            from_="",
            to="",
            date="Mon, 15 Jan 2024 10:30:00 +0000",
            labels=[],
            body="",
            attachments=[],
        )

        email = EmailMapper.to_domain(gateway_message)

        assert email.date_sent is not None
        assert email.date_sent.year == 2024
        assert email.date_sent.month == 1
        assert email.date_sent.day == 15

    def test_to_domain_empty_date(self) -> None:
        gateway_message = GmailMessage(
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

        email = EmailMapper.to_domain(gateway_message)

        assert email.date_sent is None

    def test_to_domain_multiple_recipients(self) -> None:
        gateway_message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="",
            from_="sender@example.com",
            to="one@example.com,two@example.com",
            date="",
            labels=[],
            body="",
            attachments=[],
        )

        email = EmailMapper.to_domain(gateway_message)

        assert len(email.to_addresses) == 2
        assert email.to_addresses[0] == EmailAddress("one@example.com")
        assert email.to_addresses[1] == EmailAddress("two@example.com")

    def test_to_domain_extracts_address_from_display_name(self) -> None:
        # Real Gmail headers carry display names — the mapper must extract the
        # bare address instead of choking on the RFC 5322 form.
        gateway_message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="Hi",
            from_="LinkedIn <messages-noreply@linkedin.com>",
            to="Alex <alex@example.com>, Sam <sam@example.com>",
            date="",
            labels=[],
            body="",
            attachments=[],
        )

        email = EmailMapper.to_domain(gateway_message)

        assert email.from_address == EmailAddress("messages-noreply@linkedin.com")
        assert email.to_addresses == [
            EmailAddress("alex@example.com"),
            EmailAddress("sam@example.com"),
        ]

    def test_to_domain_drops_unparseable_sender(self) -> None:
        gateway_message = GmailMessage(
            id="msg_1",
            thread_id="thread_1",
            snippet="",
            subject="",
            from_="not-an-email",
            to="",
            date="",
            labels=[],
            body="",
            attachments=[],
        )

        email = EmailMapper.to_domain(gateway_message)

        assert email.from_address is None

    def test_to_domain_empty_to(self) -> None:
        gateway_message = GmailMessage(
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

        email = EmailMapper.to_domain(gateway_message)

        assert email.to_addresses == []

    def test_to_domain_empty_from(self) -> None:
        gateway_message = GmailMessage(
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

        email = EmailMapper.to_domain(gateway_message)

        assert email.from_address is None


class TestThreadMapper:
    def test_to_domain_basic(self) -> None:
        email_id = UUIDId.generate()
        gateway_data = {
            "thread_id": "thread_1",
            "email_ids": [str(email_id)],
            "subject": "Test Thread",
            "snippet": "First message snippet",
            "participants": ["alice@example.com", "bob@example.com"],
        }

        thread = ThreadMapper.to_domain(gateway_data)

        assert isinstance(thread.id, UUIDId)
        assert thread.thread_id == ThreadId("thread_1")
        assert thread.subject == "Test Thread"
        assert thread.snippet == "First message snippet"
        assert thread.participants == ["alice@example.com", "bob@example.com"]
        assert thread.email_ids == (email_id,)

    def test_to_domain_minimal(self) -> None:
        email_id = UUIDId.generate()
        gateway_data = {
            "thread_id": "thread_2",
            "email_ids": [str(email_id)],
        }

        thread = ThreadMapper.to_domain(gateway_data)

        assert thread.thread_id == ThreadId("thread_2")
        assert thread.subject == ""
        assert thread.snippet == ""
        assert thread.participants == []

    def test_to_domain_multiple_emails(self) -> None:
        id1 = UUIDId.generate()
        id2 = UUIDId.generate()
        gateway_data = {
            "thread_id": "thread_3",
            "email_ids": [str(id1), str(id2)],
            "subject": "Multi-email thread",
        }

        thread = ThreadMapper.to_domain(gateway_data)

        assert thread.email_ids == (id1, id2)
