from __future__ import annotations

import pytest

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import DatabaseConfig, Settings
from src.Bootstrap.wiring import register_infrastructure
from src.Common.Domain.Events import EventBus, InMemoryEventBus
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Gmail.Domain.Repository.thread_repository import ThreadRepository
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Notification.Domain.Gateway.notification_gateway import NotificationGateway
from src.Search.Domain.Gateway.embedding_gateway import EmbeddingGateway


@pytest.fixture
def container() -> Container:
    settings = Settings(database=DatabaseConfig(url="sqlite://"))
    return register_infrastructure(Container(), settings)


async def test_email_repository_resolves_to_sqlite(container: Container) -> None:
    from src.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_email_repository import (
        SqliteEmailRepository,
    )

    repo = await container.resolve(EmailRepository)
    assert isinstance(repo, SqliteEmailRepository)


async def test_thread_repository_resolves(container: Container) -> None:
    assert await container.resolve(ThreadRepository) is not None


async def test_event_bus_resolves_to_in_memory(container: Container) -> None:
    assert isinstance(await container.resolve(EventBus), InMemoryEventBus)


async def test_llm_and_notification_and_embedding_resolve(container: Container) -> None:
    assert await container.resolve(LlmGateway) is not None
    assert await container.resolve(NotificationGateway) is not None
    assert await container.resolve(EmbeddingGateway) is not None


async def test_wired_repository_persists(container: Container) -> None:
    from src.Gmail.Domain.Entities.email import Email

    repo = await container.resolve(EmailRepository)
    email = Email.from_gmail_message(message_id="w1", thread_id="t1", subject="Wired")
    repo.save(email)
    assert repo.find_by_gmail_message_id("w1").subject == "Wired"


async def test_file_database_wiring_applies_migrations(tmp_path) -> None:
    # A file-backed URL goes through Alembic, not create_all, so the schema is
    # migration-managed (an alembic_version table is present).
    from sqlalchemy import create_engine, inspect

    from src.Gmail.Domain.Entities.email import Email

    url = f"sqlite:///{tmp_path / 'wired.db'}"
    settings = Settings(database=DatabaseConfig(url=url))
    container = register_infrastructure(Container(), settings)

    assert "alembic_version" in inspect(create_engine(url)).get_table_names()

    repo = await container.resolve(EmailRepository)
    repo.save(Email.from_gmail_message(message_id="f1", thread_id="t1", subject="File"))
    assert repo.find_by_gmail_message_id("f1").subject == "File"
