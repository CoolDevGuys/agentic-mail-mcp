from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from src.Common.Audit.audit_log import AuditLog
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.Persistence.audit_models import AuditLogModel


class SqliteAuditLogRepository:
    """AuditLogRepository backed by synchronous SQLAlchemy."""

    def __init__(self, session_factory: sessionmaker[Session]) -> None:
        self._session_factory = session_factory

    def save(self, entry: AuditLog) -> None:
        with self._session_factory() as session:
            session.add(
                AuditLogModel(
                    id=str(entry.id),
                    action=entry.action,
                    timestamp=entry.timestamp,
                    correlation_id=entry.correlation_id,
                    email_id=entry.email_id,
                    details=dict(entry.details),
                )
            )
            session.commit()

    def list_all(self) -> list[AuditLog]:
        with self._session_factory() as session:
            models = session.scalars(
                select(AuditLogModel).order_by(AuditLogModel.timestamp)
            ).all()
            return [self._to_domain(m) for m in models]

    @staticmethod
    def _to_domain(model: AuditLogModel) -> AuditLog:
        return AuditLog(
            id=UUIDId.from_string(model.id),
            action=model.action,
            timestamp=model.timestamp,
            correlation_id=model.correlation_id,
            email_id=model.email_id,
            details=dict(model.details or {}),
        )
