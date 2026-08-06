from __future__ import annotations

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Search.Application.UseCases.dtos import RebuildStats
from agentic_mail_mcp.Search.Application.UseCases.index_email import IndexEmailUseCase


class RebuildIndexUseCase:
    """Re-embed and re-index a set of emails.

    The caller supplies the email ids to rebuild (e.g. the currently indexed
    set); Phase 5 wires the concrete source. Each id is re-indexed via the
    IndexEmailUseCase so extraction/embedding stays in one place.
    """

    def __init__(self, index_email_use_case: IndexEmailUseCase) -> None:
        self._index_email = index_email_use_case

    def execute(self, email_ids: list[UUIDId]) -> RebuildStats:
        rebuilt = 0
        for email_id in email_ids:
            self._index_email.execute(email_id)
            rebuilt += 1
        return RebuildStats(rebuilt=rebuilt)
