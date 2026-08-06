from __future__ import annotations

from datetime import datetime

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Entities.attachment import Attachment
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Entities.label import Label
from agentic_mail_mcp.Gmail.Domain.Entities.thread import Thread, _EmailEntry
from agentic_mail_mcp.Gmail.Domain.ValueObjects import (
    EmailAddress,
    GmailMessageId,
    ThreadId,
)
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import (
    AttachmentModel,
    EmailModel,
    LabelModel,
    ThreadModel,
)


class EmailOrmMapper:
    @staticmethod
    def to_orm(email: Email) -> EmailModel:
        return EmailModel(
            id=str(email.id),
            message_id=email.message_id.value,
            thread_id=email.thread_id.value,
            snippet=email.snippet,
            subject=email.subject,
            from_address=email.from_address.value if email.from_address else None,
            to_addresses=[a.value for a in email.to_addresses],
            date_sent=email.date_sent,
            is_read=email.is_read,
            labels=sorted(email.labels),
            body=email.body,
            attachments=list(email.attachments),
            is_trashed=email.is_trashed,
        )

    @staticmethod
    def to_domain(model: EmailModel) -> Email:
        return Email(
            id=UUIDId.from_string(model.id),
            message_id=GmailMessageId(model.message_id),
            thread_id=ThreadId(model.thread_id),
            snippet=model.snippet,
            subject=model.subject,
            from_address=(
                EmailAddress(model.from_address) if model.from_address else None
            ),
            to_addresses=[EmailAddress(a) for a in model.to_addresses],
            date_sent=model.date_sent,
            is_read=model.is_read,
            _labels=set(model.labels),
            body=model.body,
            _attachments=list(model.attachments),
            _is_trashed=model.is_trashed,
        )


class ThreadOrmMapper:
    @staticmethod
    def to_orm(thread: Thread) -> ThreadModel:
        entries = [
            {"email_id": str(entry.email_id), "date_sent": entry.date_sent.isoformat()}
            for entry in thread._emails
        ]
        return ThreadModel(
            id=str(thread.id),
            thread_id=thread.thread_id.value,
            snippet=thread.snippet,
            subject=thread.subject,
            participants=list(thread.participants),
            email_entries=entries,
            last_updated=thread.last_updated,
            is_read=thread.is_read,
        )

    @staticmethod
    def to_domain(model: ThreadModel) -> Thread:
        emails = [
            _EmailEntry(
                UUIDId.from_string(entry["email_id"]),
                datetime.fromisoformat(entry["date_sent"]),
            )
            for entry in model.email_entries
        ]
        return Thread(
            id=UUIDId.from_string(model.id),
            thread_id=ThreadId(model.thread_id),
            snippet=model.snippet,
            subject=model.subject,
            participants=list(model.participants),
            _emails=emails,
            last_updated=model.last_updated,
            is_read=model.is_read,
        )


class AttachmentOrmMapper:
    @staticmethod
    def to_orm(attachment: Attachment) -> AttachmentModel:
        return AttachmentModel(
            id=str(attachment.id),
            file_name=attachment.file_name,
            mime_type=attachment.mime_type,
            size_bytes=attachment.size_bytes,
            attachment_id=attachment.attachment_id,
            download_url=attachment.download_url,
        )

    @staticmethod
    def to_domain(model: AttachmentModel) -> Attachment:
        return Attachment(
            id=UUIDId.from_string(model.id),
            file_name=model.file_name,
            mime_type=model.mime_type,
            size_bytes=model.size_bytes,
            attachment_id=model.attachment_id,
            download_url=model.download_url,
        )


class LabelOrmMapper:
    @staticmethod
    def to_orm(label: Label) -> LabelModel:
        return LabelModel(
            id=str(label.id),
            label_id=label.label_id,
            name=label.name,
            color=label.color,
            type=label.type,
        )

    @staticmethod
    def to_domain(model: LabelModel) -> Label:
        return Label(
            id=UUIDId.from_string(model.id),
            label_id=model.label_id,
            name=model.name,
            color=model.color,
            type=model.type,
        )
