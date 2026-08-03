from __future__ import annotations

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, sessionmaker

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Mappers.orm_mappers import (
    EmailOrmMapper,
)
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import EmailModel


class SqliteEmailRepository:
    """EmailRepository implementation backed by synchronous SQLAlchemy.

    ``search`` performs a simple case-insensitive substring match over the
    subject, snippet, and body; full Gmail-query parsing against the local cache
    is out of scope for this phase.
    """

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def find_by_id(self, id: UUIDId) -> Email | None:
        with self._session_factory() as session:
            model = session.get(EmailModel, str(id))
            return EmailOrmMapper.to_domain(model) if model else None

    def find_by_gmail_message_id(self, message_id: str) -> Email | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(EmailModel).where(EmailModel.message_id == message_id)
            )
            return EmailOrmMapper.to_domain(model) if model else None

    def find_by_thread_id(self, thread_id: str) -> list[Email]:
        with self._session_factory() as session:
            models = session.scalars(
                select(EmailModel).where(EmailModel.thread_id == thread_id)
            ).all()
            return [EmailOrmMapper.to_domain(m) for m in models]

    def search(self, query: str) -> list[Email]:
        pattern = f"%{query}%"
        with self._session_factory() as session:
            models = session.scalars(
                select(EmailModel).where(
                    or_(
                        EmailModel.subject.ilike(pattern),
                        EmailModel.snippet.ilike(pattern),
                        EmailModel.body.ilike(pattern),
                    )
                )
            ).all()
            return [EmailOrmMapper.to_domain(m) for m in models]

    def list_unread(self, limit: int) -> list[Email]:
        with self._session_factory() as session:
            models = session.scalars(
                select(EmailModel)
                .where(EmailModel.is_read.is_(False))
                .where(EmailModel.is_trashed.is_(False))
                .limit(limit)
            ).all()
            return [EmailOrmMapper.to_domain(m) for m in models]

    def save(self, email: Email) -> None:
        with self._session_factory() as session:
            session.merge(EmailOrmMapper.to_orm(email))
            session.commit()

    def delete(self, id: UUIDId) -> None:
        with self._session_factory() as session:
            model = session.get(EmailModel, str(id))
            if model is not None:
                session.delete(model)
                session.commit()
