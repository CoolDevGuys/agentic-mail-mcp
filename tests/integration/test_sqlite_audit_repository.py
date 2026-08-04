from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.Common.Audit.audit_log import AuditLog
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.Persistence import audit_models  # noqa: F401
from src.Common.Infrastructure.Persistence.database import (
    create_all,
    create_database_engine,
    create_session_factory,
)
from src.Common.Infrastructure.Persistence.sqlite_audit_repository import (
    SqliteAuditLogRepository,
)


@pytest.fixture
def repository():
    engine = create_database_engine("sqlite://")
    create_all(engine)
    return SqliteAuditLogRepository(create_session_factory(engine))


def _entry(action: str = "forward") -> AuditLog:
    return AuditLog(
        id=UUIDId.generate(),
        action=action,
        timestamp=datetime(2026, 8, 4, 12, 0, tzinfo=UTC),
        correlation_id="corr-1",
        email_id="email-1",
        details={"forwarded_to": "x@y.com"},
    )


class TestSqliteAuditLogRepository:
    def test_save_and_retrieve(self, repository) -> None:
        entry = _entry()
        repository.save(entry)

        stored = repository.list_all()
        assert len(stored) == 1
        assert stored[0].id == entry.id
        assert stored[0].action == "forward"
        assert stored[0].correlation_id == "corr-1"
        assert stored[0].email_id == "email-1"
        assert stored[0].details["forwarded_to"] == "x@y.com"
        assert stored[0].timestamp == entry.timestamp

    def test_list_all_ordered_by_timestamp(self, repository) -> None:
        repository.save(_entry("archive"))
        repository.save(_entry("delete"))
        assert [e.action for e in repository.list_all()] == ["archive", "delete"]
