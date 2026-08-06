from __future__ import annotations

import json
from datetime import UTC, datetime

import pytest

from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError, ValidationError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Common.Infrastructure.Clock import FrozenClock
from agentic_mail_mcp.Common.Infrastructure.IdGenerator import UuidIdGenerator
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Intelligence.Application.DTO.dtos import (
    ClassificationDTO,
    SuggestionDTO,
    SummaryDTO,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.classify_email import (
    ClassifyEmailUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.digest import (
    DailyDigestUseCase,
    WeeklyDigestUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.extract_action_items import (
    ExtractActionItemsUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.suggest_reply import (
    SuggestReplyUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.summarize_email import (
    SummarizeEmailUseCase,
)
from agentic_mail_mcp.Notification.Domain.Events.digest_ready import DigestReady
from tests.fakes.ports import (
    InMemoryClassificationRepository,
    InMemoryEmailRepository,
    InMemorySuggestionRepository,
    InMemorySummaryRepository,
    StubLlmGateway,
)


def _email(
    subject: str = "Sub", body: str = "Body", *, sent: datetime | None = None
) -> Email:
    email = Email.from_gmail_message(
        message_id="m1", thread_id="t1", subject=subject, body=body
    )
    email.date_sent = sent
    return email


class TestSummarizeEmailUseCase:
    def test_summarizes_and_persists(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        summaries = InMemorySummaryRepository()
        llm = StubLlmGateway(response_text="a short summary", model="m-1")
        uc = SummarizeEmailUseCase(
            repo, llm, summaries, FrozenClock(), UuidIdGenerator()
        )
        dto = uc.execute(email.id)

        assert isinstance(dto, SummaryDTO)
        assert dto.summary_text == "a short summary"
        assert dto.model_used == "m-1"
        assert len(summaries.saved) == 1
        assert "Sub" in llm.calls[0]["prompt"]

    def test_missing_email_raises(self) -> None:
        uc = SummarizeEmailUseCase(
            InMemoryEmailRepository(),
            StubLlmGateway(),
            InMemorySummaryRepository(),
            FrozenClock(),
            UuidIdGenerator(),
        )
        with pytest.raises(NotFoundError):
            uc.execute(UUIDId.generate())


class TestSuggestReplyUseCase:
    def test_suggests_reply(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        suggestions = InMemorySuggestionRepository()
        uc = SuggestReplyUseCase(
            repo,
            StubLlmGateway(response_text="Sure, sounds good."),
            suggestions,
            FrozenClock(),
            UuidIdGenerator(),
        )
        dto = uc.execute(email.id)
        assert isinstance(dto, SuggestionDTO)
        assert dto.suggestion_type == "reply"
        assert dto.draft_text == "Sure, sounds good."
        assert len(suggestions.saved) == 1

    def test_missing_email_raises(self) -> None:
        uc = SuggestReplyUseCase(
            InMemoryEmailRepository(),
            StubLlmGateway(),
            InMemorySuggestionRepository(),
            FrozenClock(),
            UuidIdGenerator(),
        )
        with pytest.raises(NotFoundError):
            uc.execute(UUIDId.generate())


class TestClassifyEmailUseCase:
    @pytest.mark.parametrize("category", ["urgent", "normal", "spam", "promo"])
    def test_classifies_all_categories(self, category: str) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        classifications = InMemoryClassificationRepository()
        llm = StubLlmGateway(
            response_text=json.dumps(
                {"category": category, "priority": 2, "confidence": 0.87}
            )
        )
        uc = ClassifyEmailUseCase(
            repo, llm, classifications, FrozenClock(), UuidIdGenerator()
        )
        dto = uc.execute(email.id)
        assert isinstance(dto, ClassificationDTO)
        assert dto.category == category
        assert dto.priority == 2
        assert dto.confidence == 0.87
        assert len(classifications.saved) == 1

    def test_unparseable_response_raises(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        uc = ClassifyEmailUseCase(
            repo,
            StubLlmGateway(response_text="not json"),
            InMemoryClassificationRepository(),
            FrozenClock(),
            UuidIdGenerator(),
        )
        with pytest.raises(ValidationError):
            uc.execute(email.id)

    def test_missing_email_raises(self) -> None:
        uc = ClassifyEmailUseCase(
            InMemoryEmailRepository(),
            StubLlmGateway(),
            InMemoryClassificationRepository(),
            FrozenClock(),
            UuidIdGenerator(),
        )
        with pytest.raises(NotFoundError):
            uc.execute(UUIDId.generate())


class TestExtractActionItemsUseCase:
    def test_extracts_items(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        llm = StubLlmGateway(
            response_text='[{"description": "Send report", "due_date": "2026-08-10", "priority": 1}]'
        )
        uc = ExtractActionItemsUseCase(repo, llm)
        items = uc.execute(email.id)
        assert len(items) == 1
        assert items[0].description == "Send report"
        assert items[0].due_date == "2026-08-10"
        assert items[0].priority == 1

    def test_empty_list(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        uc = ExtractActionItemsUseCase(repo, StubLlmGateway(response_text="[]"))
        assert uc.execute(email.id) == []

    def test_default_priority(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        uc = ExtractActionItemsUseCase(
            repo, StubLlmGateway(response_text='[{"description": "Reply"}]')
        )
        items = uc.execute(email.id)
        assert items[0].priority == 3
        assert items[0].due_date is None

    def test_bad_json_raises(self) -> None:
        repo = InMemoryEmailRepository()
        email = _email()
        repo.add(email)
        uc = ExtractActionItemsUseCase(repo, StubLlmGateway(response_text="{}"))
        with pytest.raises(ValidationError):
            uc.execute(email.id)

    def test_missing_email_raises(self) -> None:
        uc = ExtractActionItemsUseCase(InMemoryEmailRepository(), StubLlmGateway())
        with pytest.raises(NotFoundError):
            uc.execute(UUIDId.generate())


class TestDigestUseCases:
    def test_daily_digest_filters_by_day_and_publishes(self) -> None:
        clock = FrozenClock()
        clock.set(datetime(2026, 8, 3, 12, 0, tzinfo=UTC))
        repo = InMemoryEmailRepository()
        repo.add(_email("Today", sent=datetime(2026, 8, 3, 9, 0, tzinfo=UTC)))
        repo.add(_email("Yesterday", sent=datetime(2026, 8, 2, 9, 0, tzinfo=UTC)))
        bus = InMemoryEventBus()
        uc = DailyDigestUseCase(
            repo, StubLlmGateway(response_text="digest"), clock, bus
        )

        dto = uc.execute()
        assert dto.digest_type == "daily"
        assert dto.email_count == 1
        assert dto.digest_period == "2026-08-03"
        assert dto.items == ["Today"]
        published = [e for e in bus.published if isinstance(e, DigestReady)]
        assert len(published) == 1
        assert published[0].email_count == 1

    def test_weekly_digest_window(self) -> None:
        clock = FrozenClock()
        clock.set(datetime(2026, 8, 5, 12, 0, tzinfo=UTC))  # Wednesday
        repo = InMemoryEmailRepository()
        repo.add(_email("ThisWeek", sent=datetime(2026, 8, 4, 9, 0, tzinfo=UTC)))
        repo.add(_email("LastWeek", sent=datetime(2026, 7, 20, 9, 0, tzinfo=UTC)))
        bus = InMemoryEventBus()
        uc = WeeklyDigestUseCase(repo, StubLlmGateway(response_text="d"), clock, bus)

        dto = uc.execute()
        assert dto.digest_type == "weekly"
        assert dto.email_count == 1
        assert dto.items == ["ThisWeek"]
