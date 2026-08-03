from __future__ import annotations

import os

import pytest

from tests.integration.gmail.repository_contract import (
    EmailRepositoryContractTests,
    ThreadRepositoryContractTests,
)

_PG_DSN = os.environ.get("GMAIL_MCP_TEST_PG_DSN")

pytestmark = pytest.mark.skipif(
    _PG_DSN is None,
    reason="PostgreSQL not available; set GMAIL_MCP_TEST_PG_DSN to run these",
)


@pytest.fixture
def session_factory():
    from src.Common.Infrastructure.Persistence.database import (
        create_all,
        create_database_engine,
        create_session_factory,
    )

    engine = create_database_engine(_PG_DSN)
    create_all(engine)
    return create_session_factory(engine)


class TestPostgresEmailRepository(EmailRepositoryContractTests):
    @pytest.fixture
    def email_repo(self, session_factory):
        from src.Gmail.Infrastructure.Persistence.PostgreSQL.postgres_repositories import (
            PostgresEmailRepository,
        )

        return PostgresEmailRepository(session_factory)


class TestPostgresThreadRepository(ThreadRepositoryContractTests):
    @pytest.fixture
    def thread_repo(self, session_factory):
        from src.Gmail.Infrastructure.Persistence.PostgreSQL.postgres_repositories import (
            PostgresThreadRepository,
        )

        return PostgresThreadRepository(session_factory)
