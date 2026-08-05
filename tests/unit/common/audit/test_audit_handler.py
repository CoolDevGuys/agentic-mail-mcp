from __future__ import annotations

import pytest

from src.Common.Audit.correlation import (
    reset_correlation_id,
    set_correlation_id,
)
from src.Common.Domain.Events import InMemoryEventBus
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Application.Handlers.audit_log_handler import AuditLogHandler
from src.Gmail.Domain.Events import EmailArchived, EmailDeleted, EmailForwarded
from tests.fakes.ports import InMemoryAuditLogRepository


@pytest.fixture(autouse=True)
def _clear_correlation():
    reset_correlation_id()
    yield
    reset_correlation_id()


def _handler(
    repo: InMemoryAuditLogRepository,
) -> tuple[AuditLogHandler, InMemoryEventBus]:
    handler = AuditLogHandler(repo)
    bus = InMemoryEventBus()
    handler.register(bus)
    return handler, bus


class TestAuditLogHandler:
    def test_forward_event_produces_entry(self) -> None:
        repo = InMemoryAuditLogRepository()
        _, bus = _handler(repo)
        eid = UUIDId.generate()

        bus.publish(EmailForwarded(email_id=eid, forwarded_to="x@y.com"))

        assert len(repo.entries) == 1
        entry = repo.entries[0]
        assert entry.action == "forward"
        assert entry.email_id == str(eid)
        assert entry.details["forwarded_to"] == "x@y.com"

    def test_every_write_event_is_audited(self) -> None:
        repo = InMemoryAuditLogRepository()
        _, bus = _handler(repo)

        bus.publish(EmailArchived(email_id=UUIDId.generate()))
        bus.publish(EmailDeleted(email_id=UUIDId.generate()))

        actions = {e.action for e in repo.entries}
        assert actions == {"archive", "delete"}

    def test_correlation_id_is_preserved(self) -> None:
        repo = InMemoryAuditLogRepository()
        _, bus = _handler(repo)
        set_correlation_id("corr-123")

        bus.publish(EmailArchived(email_id=UUIDId.generate()))

        assert repo.entries[0].correlation_id == "corr-123"

    def test_correlation_id_generated_when_absent(self) -> None:
        repo = InMemoryAuditLogRepository()
        _, bus = _handler(repo)

        bus.publish(EmailArchived(email_id=UUIDId.generate()))

        assert repo.entries[0].correlation_id  # non-empty generated id
