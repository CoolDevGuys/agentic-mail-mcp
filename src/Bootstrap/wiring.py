"""Registers the default infrastructure adapters on the DI container.

Default stack: synchronous SQLite persistence, in-memory event bus, BGE
embeddings, OpenAI-compatible LLM, and webhook notifications. The Gmail gateway
and the vector repository require runtime resources (OAuth credentials, a SQLite
build with extension loading), so they are wired at startup by the caller rather
than registered as always-constructible defaults here.
"""

from __future__ import annotations

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import Settings
from src.Common.Domain.Events import EventBus, InMemoryEventBus
from src.Common.Infrastructure.Persistence.database import (
    create_all,
    create_database_engine,
    create_session_factory,
)
from src.Common.Infrastructure.Persistence.migrations_runner import apply_migrations
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Gmail.Domain.Repository.thread_repository import ThreadRepository
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Models import models  # noqa: F401
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_email_repository import (
    SqliteEmailRepository,
)
from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_thread_repository import (
    SqliteThreadRepository,
)
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Intelligence.Infrastructure.LlamaCpp.llama_cpp_gateway import LlamaCppGateway
from src.Notification.Domain.Gateway.notification_gateway import NotificationGateway
from src.Notification.Infrastructure.Webhook.webhook_notification_gateway import (
    WebhookNotificationGateway,
)
from src.Search.Domain.Gateway.embedding_gateway import EmbeddingGateway
from src.Search.Infrastructure.BGE.bge_embedding_gateway import BgeEmbeddingGateway


def _is_in_memory(url: str) -> bool:
    return url in ("sqlite://", "sqlite:///:memory:")


def register_infrastructure(container: Container, settings: Settings) -> Container:
    engine = create_database_engine(settings.database.url)
    if _is_in_memory(settings.database.url):
        # Alembic opens its own connection, which for in-memory SQLite is a
        # separate database; create the schema on this engine directly.
        create_all(engine)
    else:
        # Migrations are the single source of truth for file/server databases.
        apply_migrations(settings.database.url)
    session_factory = create_session_factory(engine)

    # Registering a port (Protocol) -> implementation is the intended DI mapping;
    # mypy's type-abstract check is a false positive for service-locator keys.
    container.register(EventBus, InMemoryEventBus)  # type: ignore[type-abstract]
    container.register(
        EmailRepository,  # type: ignore[type-abstract]
        lambda: SqliteEmailRepository(session_factory),
    )
    container.register(
        ThreadRepository,  # type: ignore[type-abstract]
        lambda: SqliteThreadRepository(session_factory),
    )
    container.register(
        EmbeddingGateway,  # type: ignore[type-abstract]
        lambda: BgeEmbeddingGateway(
            model_name=settings.search.embedding_model,
            dimension=settings.search.embedding_dimension,
        ),
    )
    container.register(
        LlmGateway,  # type: ignore[type-abstract]
        lambda: LlamaCppGateway.from_settings(settings),
    )
    container.register(
        NotificationGateway,  # type: ignore[type-abstract]
        lambda: WebhookNotificationGateway(settings.notifications.webhook_url),
    )
    return container
