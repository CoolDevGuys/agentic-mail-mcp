from __future__ import annotations

from dataclasses import dataclass, field

from src.Intelligence.Domain.Entities.classification import Classification
from src.Intelligence.Domain.Entities.suggestion import Suggestion
from src.Intelligence.Domain.Entities.summary import Summary


@dataclass(frozen=True)
class SummaryDTO:
    id: str
    email_id: str
    summary_text: str
    model_used: str

    @classmethod
    def from_entity(cls, summary: Summary) -> SummaryDTO:
        return cls(
            id=str(summary.id),
            email_id=str(summary.email_id),
            summary_text=summary.summary_text,
            model_used=summary.model_used,
        )


@dataclass(frozen=True)
class SuggestionDTO:
    id: str
    email_id: str
    suggestion_type: str
    draft_text: str | None
    model_used: str

    @classmethod
    def from_entity(cls, suggestion: Suggestion) -> SuggestionDTO:
        return cls(
            id=str(suggestion.id),
            email_id=str(suggestion.email_id),
            suggestion_type=suggestion.suggestion_type,
            draft_text=suggestion.draft_text,
            model_used=suggestion.model_used,
        )


@dataclass(frozen=True)
class ClassificationDTO:
    id: str
    email_id: str
    category: str
    priority: int
    confidence: float
    model_used: str

    @classmethod
    def from_entity(cls, classification: Classification) -> ClassificationDTO:
        return cls(
            id=str(classification.id),
            email_id=str(classification.email_id),
            category=classification.category,
            priority=classification.priority,
            confidence=classification.confidence,
            model_used=classification.model_used,
        )


@dataclass(frozen=True)
class ActionItemDTO:
    description: str
    due_date: str | None = None
    priority: int = 3


@dataclass(frozen=True)
class DigestDTO:
    digest_type: str
    digest_period: str
    email_count: int
    summary_text: str
    items: list[str] = field(default_factory=list)
