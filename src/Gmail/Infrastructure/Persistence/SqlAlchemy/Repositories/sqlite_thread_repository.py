from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.thread import Thread
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Mappers.orm_mappers import (
    ThreadOrmMapper,
)
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Models.models import ThreadModel


class SqliteThreadRepository:
    """ThreadRepository implementation backed by synchronous SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def find_by_id(self, id: UUIDId) -> Thread | None:
        with self._session_factory() as session:
            model = session.get(ThreadModel, str(id))
            return ThreadOrmMapper.to_domain(model) if model else None

    def find_by_gmail_thread_id(self, thread_id: str) -> Thread | None:
        with self._session_factory() as session:
            model = session.scalar(
                select(ThreadModel).where(ThreadModel.thread_id == thread_id)
            )
            return ThreadOrmMapper.to_domain(model) if model else None

    def save(self, thread: Thread) -> None:
        with self._session_factory() as session:
            session.merge(ThreadOrmMapper.to_orm(thread))
            session.commit()

    def delete(self, id: UUIDId) -> None:
        with self._session_factory() as session:
            model = session.get(ThreadModel, str(id))
            if model is not None:
                session.delete(model)
                session.commit()
