from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentic_mail_mcp.Intelligence.Domain.Entities.classification import Classification
from agentic_mail_mcp.Intelligence.Domain.Entities.suggestion import Suggestion
from agentic_mail_mcp.Intelligence.Domain.Entities.summary import Summary


@runtime_checkable
class SummaryRepository(Protocol):
    def save(self, summary: Summary) -> None: ...


@runtime_checkable
class ClassificationRepository(Protocol):
    def save(self, classification: Classification) -> None: ...


@runtime_checkable
class SuggestionRepository(Protocol):
    def save(self, suggestion: Suggestion) -> None: ...
