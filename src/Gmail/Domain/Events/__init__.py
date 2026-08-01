from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime

from src.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass
class EmailReceived:
    email_id: UUIDId
    from_address: str
    subject: str
    received_at: datetime


@dataclass
class EmailRead:
    email_id: UUIDId
    read_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmailArchived:
    email_id: UUIDId
    archived_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmailDeleted:
    email_id: UUIDId
    deleted_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmailForwarded:
    email_id: UUIDId
    forwarded_to: str
    forwarded_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class EmailLabeled:
    email_id: UUIDId
    label_name: str
    labeled_at: datetime = field(default_factory=lambda: datetime.now(UTC))


@dataclass
class InboxSynchronized:
    history_id: str
    synchronized_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    email_count: int = 0
