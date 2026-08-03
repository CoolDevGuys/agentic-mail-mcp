"""PostgreSQL repository variants.

The synchronous SQLAlchemy repositories are driver-agnostic, so the PostgreSQL
variants reuse the same implementation against a PostgreSQL engine. They exist
as distinct types to make the backend explicit at wiring time and share the
single Alembic migration (portable DDL) with SQLite.
"""

from __future__ import annotations

from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_email_repository import (
    SqliteEmailRepository,
)
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_thread_repository import (
    SqliteThreadRepository,
)


class PostgresEmailRepository(SqliteEmailRepository):
    """EmailRepository backed by PostgreSQL (same SQLAlchemy implementation)."""


class PostgresThreadRepository(SqliteThreadRepository):
    """ThreadRepository backed by PostgreSQL (same SQLAlchemy implementation)."""
