from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Intelligence.Domain.Entities import Classification, Suggestion, Summary


class TestSummary:
    def test_create_valid_summary(self) -> None:
        summary = Summary(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            summary_text="Meeting at 3pm",
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )

        assert summary.summary_text == "Meeting at 3pm"
        assert summary.model_used == "gpt-4"

    def test_empty_summary_text_raises(self) -> None:
        with pytest.raises(ValidationError, match="summary_text must not be empty"):
            Summary(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                summary_text="",
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_whitespace_only_summary_text_raises(self) -> None:
        with pytest.raises(ValidationError, match="summary_text must not be empty"):
            Summary(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                summary_text="   ",
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )


class TestClassification:
    def test_create_valid_classification(self) -> None:
        classification = Classification(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            category="urgent",
            priority=3,
            confidence=0.85,
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )

        assert classification.category == "urgent"
        assert classification.priority == 3
        assert classification.confidence == 0.85

    @pytest.mark.parametrize("category", ["urgent", "normal", "spam", "promo"])
    def test_valid_categories(self, category: str) -> None:
        c = Classification(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            category=category,
            priority=1,
            confidence=0.5,
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )
        assert c.category == category

    def test_invalid_category_raises(self) -> None:
        with pytest.raises(ValidationError, match="category must be one of"):
            Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="unknown",
                priority=3,
                confidence=0.5,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_priority_below_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="priority must be between 1 and 5"):
            Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=0,
                confidence=0.5,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_priority_above_range_raises(self) -> None:
        with pytest.raises(ValidationError, match="priority must be between 1 and 5"):
            Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=6,
                confidence=0.5,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_confidence_below_range_raises(self) -> None:
        with pytest.raises(
            ValidationError, match="confidence must be between 0.0 and 1.0"
        ):
            Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=3,
                confidence=-0.1,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_confidence_above_range_raises(self) -> None:
        with pytest.raises(
            ValidationError, match="confidence must be between 0.0 and 1.0"
        ):
            Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=3,
                confidence=1.5,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )

    def test_boundary_priority_values(self) -> None:
        for p in (1, 5):
            c = Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=p,
                confidence=0.5,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )
            assert c.priority == p

    def test_boundary_confidence_values(self) -> None:
        for conf in (0.0, 1.0):
            c = Classification(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                category="normal",
                priority=3,
                confidence=conf,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )
            assert c.confidence == conf


class TestSuggestion:
    def test_create_valid_suggestion(self) -> None:
        suggestion = Suggestion(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            suggestion_type="reply",
            draft_text="Thanks for the update.",
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )

        assert suggestion.suggestion_type == "reply"
        assert suggestion.draft_text == "Thanks for the update."

    def test_create_suggestion_without_draft(self) -> None:
        suggestion = Suggestion(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            suggestion_type="ignore",
            draft_text=None,
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )

        assert suggestion.suggestion_type == "ignore"
        assert suggestion.draft_text is None

    @pytest.mark.parametrize("stype", ["reply", "forward", "ignore"])
    def test_valid_suggestion_types(self, stype: str) -> None:
        s = Suggestion(
            id=UUIDId.generate(),
            email_id=UUIDId.generate(),
            suggestion_type=stype,
            draft_text=None,
            model_used="gpt-4",
            created_at=datetime.now(UTC),
        )
        assert s.suggestion_type == stype

    def test_invalid_suggestion_type_raises(self) -> None:
        with pytest.raises(ValidationError, match="suggestion_type must be one of"):
            Suggestion(
                id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                suggestion_type="delete",
                draft_text=None,
                model_used="gpt-4",
                created_at=datetime.now(UTC),
            )
