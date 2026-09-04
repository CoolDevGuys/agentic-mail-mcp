"""Shared builder for MCP-layer unit tests.

Assembles an ``McpUseCases`` bundle from the in-memory fakes in
``tests/fakes/ports`` so tool, registry, resource, and server tests can drive
the real use cases and assert against the recorded fake state.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
from agentic_mail_mcp.Common.Infrastructure.Clock import SystemClock
from agentic_mail_mcp.Common.Infrastructure.IdGenerator import UuidIdGenerator
from agentic_mail_mcp.Common.Railguards.config import RailguardConfig
from agentic_mail_mcp.Common.Railguards.validator import RailguardValidator
from agentic_mail_mcp.Gmail.Application.UseCases.add_label import AddLabelUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.archive_email import (
    ArchiveEmailUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.delete_email import DeleteEmailUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.drafts import (
    CreateDraftUseCase,
    SendDraftUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.forward_email import (
    ForwardEmailUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.get_email import GetEmailUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.get_thread import GetThreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_labels import ListLabelsUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_unread import ListUnreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.search_emails import (
    SearchEmailsUseCase,
)
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
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
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases
from agentic_mail_mcp.Search.Application.UseCases.semantic_search import (
    SemanticSearchUseCase,
)
from tests.fakes.ports import (
    InMemoryClassificationRepository,
    InMemoryEmailRepository,
    InMemorySuggestionRepository,
    InMemorySummaryRepository,
    InMemoryVectorSearchRepository,
    StubEmbeddingGateway,
    StubGmailGateway,
    StubLlmGateway,
)


@dataclass
class McpEnv:
    uses: McpUseCases
    email_repo: InMemoryEmailRepository
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
        get_thread=GetThreadUseCase(gateway),
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
        semantic_search=SemanticSearchUseCase(
            embedding, vector_repo, email_repository=email_repo
        ),
    )
    return McpEnv(
        uses=uses,
        email_repo=email_repo,
        gateway=gateway,
        event_bus=event_bus,
        llm=llm,
        embedding=embedding,
        vector_repo=vector_repo,
    )


@pytest.fixture
def env() -> McpEnv:
    return make_env()
