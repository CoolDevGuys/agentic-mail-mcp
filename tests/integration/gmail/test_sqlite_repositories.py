from __future__ import annotations

import pytest

from agentic_mail_mcp.Common.Infrastructure.Persistence.database import (
    create_all,
    create_database_engine,
    create_session_factory,
)
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_email_repository import (
    SqliteEmailRepository,
)
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_thread_repository import (
    SqliteThreadRepository,
)
from tests.integration.gmail.repository_contract import (
    EmailRepositoryContractTests,
    ThreadRepositoryContractTests,
)


@pytest.fixture
def session_factory():
    engine = create_database_engine("sqlite://")
    create_all(engine)
    return create_session_factory(engine)


class TestSqliteEmailRepository(EmailRepositoryContractTests):
    @pytest.fixture
    def email_repo(self, session_factory):
        return SqliteEmailRepository(session_factory)


class TestSqliteThreadRepository(ThreadRepositoryContractTests):
    @pytest.fixture
    def thread_repo(self, session_factory):
        return SqliteThreadRepository(session_factory)
