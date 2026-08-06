"""Synchronous SQLAlchemy engine/session wiring.

The repository ports (Phase 3) and use cases (Phase 4) are synchronous, so the
persistence layer uses the synchronous SQLAlchemy engine.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import DateTime, Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.types import TypeDecorator


class Base(DeclarativeBase):
    """Declarative base shared by all ORM models."""


class UtcDateTime(TypeDecorator):
    """Timezone-aware datetime stored and returned as UTC.

    SQLite drops ``tzinfo`` from DateTime columns; the domain is uniformly
    UTC-aware, so this decorator normalizes to UTC on write and re-attaches UTC
    on read, giving consistent behavior across SQLite and PostgreSQL.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(
        self, value: datetime | None, dialect: Any
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)

    def process_result_value(
        self, value: datetime | None, dialect: Any
    ) -> datetime | None:
        if value is None:
            return None
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


def create_database_engine(url: str) -> Engine:
    """Create a synchronous engine, configuring SQLite for cross-thread use.

    In-memory SQLite keeps a single connection (StaticPool) so the schema and
    data persist across sessions within a process.
    """
    if url.startswith("sqlite"):
        connect_args = {"check_same_thread": False}
        if url in ("sqlite://", "sqlite:///:memory:"):
            return create_engine(
                url,
                future=True,
                connect_args=connect_args,
                poolclass=StaticPool,
            )
        return create_engine(url, future=True, connect_args=connect_args)
    return create_engine(url, future=True)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, expire_on_commit=False, future=True)


def create_all(engine: Engine) -> None:
    """Create all tables for models registered on Base.metadata.

    Callers must import the ORM models before invoking this so their tables are
    registered on the shared metadata.
    """
    Base.metadata.create_all(engine)
