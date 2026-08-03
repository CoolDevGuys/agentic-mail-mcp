from __future__ import annotations

from datetime import datetime, time, timedelta

from src.Common.Domain.Events import EventBus
from src.Common.Infrastructure.Clock import Clock
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Intelligence.Application.DTO.dtos import DigestDTO
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Intelligence.Domain.ValueObjects.prompt_template import PromptTemplate
from src.Notification.Domain.Events.digest_ready import DigestReady

_SYSTEM_PROMPT = "You write concise digests of a batch of emails."
_TEMPLATE = PromptTemplate(
    name="digest",
    template="Write a {period} digest for these {count} emails:\n{subjects}",
)


class _BaseDigestUseCase:
    digest_type: str = "daily"

    def __init__(
        self,
        email_repository: EmailRepository,
        llm: LlmGateway,
        clock: Clock,
        event_bus: EventBus,
        *,
        model: str = "default",
        max_tokens: int = 1024,
        fetch_limit: int = 100,
    ) -> None:
        self._email_repository = email_repository
        self._llm = llm
        self._clock = clock
        self._event_bus = event_bus
        self._model = model
        self._max_tokens = max_tokens
        self._fetch_limit = fetch_limit

    def _window(self, now: datetime) -> tuple[datetime, datetime]:
        raise NotImplementedError

    def _period_label(self, start: datetime, end: datetime) -> str:
        raise NotImplementedError

    def execute(self) -> DigestDTO:
        now = self._clock.now()
        start, end = self._window(now)
        candidates = self._email_repository.list_unread(self._fetch_limit)
        selected = [
            e
            for e in candidates
            if e.date_sent is not None and start <= e.date_sent < end
        ]
        subjects = [e.subject for e in selected]
        period = self._period_label(start, end)

        prompt = _TEMPLATE.render(
            period=self.digest_type,
            count=len(selected),
            subjects="\n".join(subjects),
        )
        response = self._llm.generate(
            prompt, _SYSTEM_PROMPT, self._max_tokens, self._model
        )

        self._event_bus.publish(
            DigestReady(
                digest_type=self.digest_type,
                digest_period=period,
                email_count=len(selected),
            )
        )
        return DigestDTO(
            digest_type=self.digest_type,
            digest_period=period,
            email_count=len(selected),
            summary_text=response.text,
            items=subjects,
        )


class DailyDigestUseCase(_BaseDigestUseCase):
    digest_type = "daily"

    def _window(self, now: datetime) -> tuple[datetime, datetime]:
        start = datetime.combine(now.date(), time.min, tzinfo=now.tzinfo)
        return start, start + timedelta(days=1)

    def _period_label(self, start: datetime, end: datetime) -> str:
        return start.date().isoformat()


class WeeklyDigestUseCase(_BaseDigestUseCase):
    digest_type = "weekly"

    def _window(self, now: datetime) -> tuple[datetime, datetime]:
        monday = now.date() - timedelta(days=now.weekday())
        start = datetime.combine(monday, time.min, tzinfo=now.tzinfo)
        return start, start + timedelta(days=7)

    def _period_label(self, start: datetime, end: datetime) -> str:
        return f"{start.date().isoformat()}/{(end - timedelta(days=1)).date().isoformat()}"
