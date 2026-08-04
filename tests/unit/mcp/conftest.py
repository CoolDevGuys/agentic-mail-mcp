"""Shared builder for MCP-layer unit tests.

Assembles an ``McpUseCases`` bundle from the in-memory fakes in
``tests/fakes/ports`` so tool, registry, resource, and server tests can drive
the real use cases and assert against the recorded fake state.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from src.Common.Domain.Events import InMemoryEventBus
from src.Common.Infrastructure.Clock import SystemClock
from src.Common.Infrastructure.IdGenerator import UuidIdGenerator
from src.Common.Railguards.config import RailguardConfig
from src.Common.Railguards.validator import RailguardValidator
from src.Gmail.Application.UseCases.add_label import AddLabelUseCase
from src.Gmail.Application.UseCases.archive_email import ArchiveEmailUseCase
from src.Gmail.Application.UseCases.delete_email import DeleteEmailUseCase
from src.Gmail.Application.UseCases.drafts import CreateDraftUseCase, SendDraftUseCase
from src.Gmail.Application.UseCases.forward_email import ForwardEmailUseCase
from src.Gmail.Application.UseCases.get_email import GetEmailUseCase
from src.Gmail.Application.UseCases.get_thread import GetThreadUseCase
from src.Gmail.Application.UseCases.list_labels import ListLabelsUseCase
from src.Gmail.Application.UseCases.list_unread import ListUnreadUseCase
from src.Gmail.Application.UseCases.search_emails import SearchEmailsUseCase
from src.Gmail.Domain.Entities.email import Email
from src.Intelligence.Application.UseCases.classify_email import ClassifyEmailUseCase
from src.Intelligence.Application.UseCases.digest import (
    DailyDigestUseCase,
    WeeklyDigestUseCase,
)
from src.Intelligence.Application.UseCases.extract_action_items import (
    ExtractActionItemsUseCase,
)
from src.Intelligence.Application.UseCases.suggest_reply import SuggestReplyUseCase
from src.Intelligence.Application.UseCases.summarize_email import SummarizeEmailUseCase
from src.MCP.Tools.use_cases import McpUseCases
from src.Search.Application.UseCases.semantic_search import SemanticSearchUseCase
from tests.fakes.ports import (
    InMemoryClassificationRepository,
    InMemoryEmailRepository,
    InMemorySuggestionRepository,
    InMemorySummaryRepository,
    InMemoryThreadRepository,
    InMemoryVectorSearchRepository,
    StubEmbeddingGateway,
    StubGmailGateway,
    StubLlmGateway,
)


@dataclass
class McpEnv:
    uses: McpUseCases
    email_repo: InMemoryEmailRepository
    thread_repo: InMemoryThreadRepository
    gateway: StubGmailGateway
    event_bus: InMemoryEventBus
    llm: StubLlmGateway
    embedding: StubEmbeddingGateway
    vector_repo: InMemoryVectorSearchRepository

    def add_email(self, message_id: str = "m1", *, labels=None) -> Email:
        email = Email.from_gmail_message(
            message_id=message_id,
            thread_id="t1",
            subject="Hello",
            from_address="sender@example.com",
            body="Body",
            labels=labels if labels is not None else ["INBOX"],
        )
        self.email_repo.add(email)
        return email


def make_env(
    *,
    access_level: str = "read_write",
    allowed_recipients: list[str] | None = None,
    rate_limits: dict[str, int] | None = None,
    llm_text: str = "stub output",
) -> McpEnv:
    email_repo = InMemoryEmailRepository()
    thread_repo = InMemoryThreadRepository()
    gateway = StubGmailGateway()
    event_bus = InMemoryEventBus()
    llm = StubLlmGateway(response_text=llm_text)
    embedding = StubEmbeddingGateway()
    vector_repo = InMemoryVectorSearchRepository()
    clock = SystemClock()
    id_gen = UuidIdGenerator()
    validator = RailguardValidator(
        RailguardConfig(
            access_level=access_level,
            allowed_recipients=allowed_recipients or [],
            rate_limits=rate_limits or {},
        )
    )

    uses = McpUseCases(
        search_emails=SearchEmailsUseCase(gateway, email_repo),
        get_email=GetEmailUseCase(gateway, email_repo),
        get_thread=GetThreadUseCase(thread_repo),
        list_unread=ListUnreadUseCase(email_repo),
        list_labels=ListLabelsUseCase(gateway),
        forward_email=ForwardEmailUseCase(gateway, validator, email_repo, event_bus),
        archive_email=ArchiveEmailUseCase(gateway, validator, email_repo, event_bus),
        delete_email=DeleteEmailUseCase(gateway, validator, email_repo, event_bus),
        create_draft=CreateDraftUseCase(gateway, validator),
        send_draft=SendDraftUseCase(gateway, validator),
        add_label=AddLabelUseCase(gateway, validator, email_repo, event_bus),
        summarize_email=SummarizeEmailUseCase(
            email_repo, llm, InMemorySummaryRepository(), clock, id_gen
        ),
        classify_email=ClassifyEmailUseCase(
            email_repo, llm, InMemoryClassificationRepository(), clock, id_gen
        ),
        suggest_reply=SuggestReplyUseCase(
            email_repo, llm, InMemorySuggestionRepository(), clock, id_gen
        ),
        extract_action_items=ExtractActionItemsUseCase(email_repo, llm),
        daily_digest=DailyDigestUseCase(email_repo, llm, clock, event_bus),
        weekly_digest=WeeklyDigestUseCase(email_repo, llm, clock, event_bus),
        semantic_search=SemanticSearchUseCase(embedding, vector_repo),
    )
    return McpEnv(
        uses=uses,
        email_repo=email_repo,
        thread_repo=thread_repo,
        gateway=gateway,
        event_bus=event_bus,
        llm=llm,
        embedding=embedding,
        vector_repo=vector_repo,
    )


@pytest.fixture
def env() -> McpEnv:
    return make_env()
