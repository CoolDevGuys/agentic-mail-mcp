from __future__ import annotations

from dataclasses import dataclass

from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)


@dataclass(frozen=True)
class SearchResultDTO:
    document_id: str
    # Internal cache UUID — not directly usable with Gmail-facing tools.
    email_id: str
    score: float
    metadata: dict[str, str]
    # Gmail message id of the matched email (fetchable via get_email), None
    # when the email cannot be resolved from the local repository.
    message_id: str | None = None

    @classmethod
    def from_result(
        cls, result: SearchResult, message_id: str | None = None
    ) -> SearchResultDTO:
        return cls(
            document_id=str(result.document_id),
            email_id=str(result.email_id),
            score=result.score,
            metadata=dict(result.metadata),
            message_id=message_id,
        )


@dataclass(frozen=True)
class RebuildStats:
    rebuilt: int
