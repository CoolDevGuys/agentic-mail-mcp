from __future__ import annotations

from datetime import datetime

from sqlalchemy import JSON, Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from agentic_mail_mcp.Common.Infrastructure.Persistence.database import (
    Base,
    UtcDateTime,
)


class EmailModel(Base):
    __tablename__ = "emails"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    message_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    thread_id: Mapped[str] = mapped_column(String(255), index=True)
    snippet: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    from_address: Mapped[str | None] = mapped_column(String(320), nullable=True)
    to_addresses: Mapped[list[str]] = mapped_column(JSON, default=list)
    date_sent: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    labels: Mapped[list[str]] = mapped_column(JSON, default=list)
    body: Mapped[str] = mapped_column(Text, default="")
    attachments: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Nested message/rfc822 parts (originals of a forward), as
    # {"subject", "from_address", "date_sent", "body"} dicts.
    attached_messages: Mapped[list[dict]] = mapped_column(JSON, default=list)
    is_trashed: Mapped[bool] = mapped_column(Boolean, default=False)


class ThreadModel(Base):
    __tablename__ = "threads"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    thread_id: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    snippet: Mapped[str] = mapped_column(Text, default="")
    subject: Mapped[str] = mapped_column(Text, default="")
    participants: Mapped[list[str]] = mapped_column(JSON, default=list)
    # Ordered list of {"email_id": str, "date_sent": iso8601}.
    email_entries: Mapped[list[dict]] = mapped_column(JSON, default=list)
    last_updated: Mapped[datetime | None] = mapped_column(UtcDateTime, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)


class AttachmentModel(Base):
    __tablename__ = "attachments"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    file_name: Mapped[str] = mapped_column(String(1024), default="")
    mime_type: Mapped[str] = mapped_column(String(255), default="")
    size_bytes: Mapped[int] = mapped_column(Integer, default=0)
    attachment_id: Mapped[str] = mapped_column(String(255), default="")
    download_url: Mapped[str] = mapped_column(Text, default="")


class LabelModel(Base):
    __tablename__ = "labels"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    label_id: Mapped[str] = mapped_column(String(255), index=True)
    name: Mapped[str] = mapped_column(String(255), default="")
    color: Mapped[str] = mapped_column(String(64), default="")
    type: Mapped[str] = mapped_column(String(32), default="user")
