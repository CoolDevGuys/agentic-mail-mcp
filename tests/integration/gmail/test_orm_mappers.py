from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Common.Infrastructure.Persistence.database import (
    create_all,
    create_database_engine,
    create_session_factory,
)
from agentic_mail_mcp.Gmail.Domain.Entities.attachment import Attachment
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Entities.label import Label
from agentic_mail_mcp.Gmail.Domain.Entities.thread import Thread
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId, ThreadId
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Mappers.orm_mappers import (
    AttachmentOrmMapper,
    EmailOrmMapper,
    LabelOrmMapper,
    ThreadOrmMapper,
)


@pytest.fixture
def session_factory():
    engine = create_database_engine("sqlite://")
    create_all(engine)
    return create_session_factory(engine)


class TestEmailOrmMapper:
    def test_round_trip_through_database(self, session_factory) -> None:
        email = Email.from_gmail_message(
            message_id="msg_1",
            thread_id="thread_1",
            subject="Hello",
            from_address="sender@example.com",
            to_addresses=["a@example.com", "b@example.com"],
            body="Body text",
            labels=["INBOX", "Work"],
        )
        email.date_sent = datetime(2026, 1, 2, 9, 30, tzinfo=UTC)
        email.mark_read()

        with session_factory() as session:
            session.add(EmailOrmMapper.to_orm(email))
            session.commit()

        with session_factory() as session:
            from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import (
                EmailModel,
            )

            model = session.get(EmailModel, str(email.id))
            restored = EmailOrmMapper.to_domain(model)

        assert restored.id == email.id
        assert restored.message_id == GmailMessageId("msg_1")
        assert restored.thread_id == ThreadId("thread_1")
        assert restored.subject == "Hello"
        assert restored.from_address == email.from_address
        assert [a.value for a in restored.to_addresses] == [
            "a@example.com",
            "b@example.com",
        ]
        assert restored.labels == frozenset({"INBOX", "Work"})
        assert restored.is_read is True
        assert restored.body == "Body text"
        assert restored.date_sent == email.date_sent

    def test_missing_from_address_round_trips_as_none(self, session_factory) -> None:
        email = Email.from_gmail_message(message_id="m2", thread_id="t2")
        model = EmailOrmMapper.to_orm(email)
        restored = EmailOrmMapper.to_domain(model)
        assert restored.from_address is None
        assert restored.to_addresses == []

    def test_attached_messages_round_trip_through_database(self, session_factory) -> None:
        from agentic_mail_mcp.Gmail.Domain.ValueObjects import (
            AttachedMessage,
            EmailAddress,
        )

        email = Email.from_gmail_message(
            message_id="msg_fwd",
            thread_id="thread_1",
            subject="Fwd: Original",
            from_address="forwarder@example.com",
            body="Forwarding note",
            attached_messages=[
                AttachedMessage(
                    subject="Original",
                    from_address=EmailAddress("original@example.com"),
                    date_sent=datetime(2026, 1, 2, 9, 30, tzinfo=UTC),
                    body="Original body",
                )
            ],
        )

        with session_factory() as session:
            session.add(EmailOrmMapper.to_orm(email))
            session.commit()

        with session_factory() as session:
            from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import (
                EmailModel,
            )

            model = session.get(EmailModel, str(email.id))
            restored = EmailOrmMapper.to_domain(model)

        assert len(restored.attached_messages) == 1
        attached = restored.attached_messages[0]
        assert attached.subject == "Original"
        assert attached.from_address == EmailAddress("original@example.com")
        assert attached.body == "Original body"
        assert attached.date_sent == datetime(2026, 1, 2, 9, 30, tzinfo=UTC)


class TestThreadOrmMapper:
    def test_round_trip_preserves_ordered_email_ids(self, session_factory) -> None:
        e1, e2 = UUIDId.generate(), UUIDId.generate()
        thread = Thread.create(
            thread_id=ThreadId("t1"),
            email_ids=[e1, e2],
            subject="Subj",
            participants=["x@example.com"],
        )

        with session_factory() as session:
            session.add(ThreadOrmMapper.to_orm(thread))
            session.commit()

        with session_factory() as session:
            from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import (
                ThreadModel,
            )

            model = session.get(ThreadModel, str(thread.id))
            restored = ThreadOrmMapper.to_domain(model)

        assert restored.id == thread.id
        assert restored.thread_id == ThreadId("t1")
        assert restored.subject == "Subj"
        assert restored.participants == ["x@example.com"]
        assert restored.email_ids == (e1, e2)


class TestAttachmentOrmMapper:
    def test_round_trip(self) -> None:
        attachment = Attachment(
            id=UUIDId.generate(),
            file_name="report.pdf",
            mime_type="application/pdf",
            size_bytes=2048,
            attachment_id="att_1",
            download_url="https://example.com/a",
        )
        restored = AttachmentOrmMapper.to_domain(AttachmentOrmMapper.to_orm(attachment))
        assert restored.id == attachment.id
        assert restored.file_name == "report.pdf"
        assert restored.mime_type == "application/pdf"
        assert restored.size_bytes == 2048
        assert restored.attachment_id == "att_1"
        assert restored.download_url == "https://example.com/a"


class TestLabelOrmMapper:
    def test_round_trip_system_label(self) -> None:
        label = Label(
            id=UUIDId.generate(), label_id="INBOX", name="INBOX", type="system"
        )
        restored = LabelOrmMapper.to_domain(LabelOrmMapper.to_orm(label))
        assert restored.id == label.id
        assert restored.label_id == "INBOX"
        assert restored.name == "INBOX"
        assert restored.type == "system"
        assert restored.is_system is True
