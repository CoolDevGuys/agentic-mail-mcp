"""In-memory Intelligence repositories.

Summaries, classifications, and suggestions are derived LLM outputs. V1 keeps
them in process memory (they can always be regenerated); durable persistence is
a later enhancement behind the same repository ports.
"""

from __future__ import annotations

from agentic_mail_mcp.Intelligence.Domain.Entities.classification import Classification
from agentic_mail_mcp.Intelligence.Domain.Entities.suggestion import Suggestion
from agentic_mail_mcp.Intelligence.Domain.Entities.summary import Summary


class InMemorySummaryRepository:
    def __init__(self) -> None:
        self._items: list[Summary] = []

    def save(self, summary: Summary) -> None:
        self._items.append(summary)


class InMemoryClassificationRepository:
    def __init__(self) -> None:
        self._items: list[Classification] = []

    def save(self, classification: Classification) -> None:
        self._items.append(classification)


class InMemorySuggestionRepository:
    def __init__(self) -> None:
        self._items: list[Suggestion] = []

    def save(self, suggestion: Suggestion) -> None:
        self._items.append(suggestion)
