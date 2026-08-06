from __future__ import annotations

import sqlite3

import pytest

from tests.integration.search.vector_contract import (
    VectorSearchRepositoryContractTests,
)


def _extension_loading_available() -> bool:
    try:
        import sqlite_vec  # noqa: F401
    except ImportError:
        return False
    conn = sqlite3.connect(":memory:")
    if not hasattr(conn, "enable_load_extension"):
        return False
    try:
        conn.enable_load_extension(True)
    except (AttributeError, sqlite3.OperationalError):
        return False
    return True


pytestmark = pytest.mark.skipif(
    not _extension_loading_available(),
    reason="sqlite-vec unavailable or this Python's sqlite3 lacks extension loading",
)


class TestSqliteVecRepository(VectorSearchRepositoryContractTests):
    @pytest.fixture
    def vector_repo(self):
        from agentic_mail_mcp.Search.Infrastructure.SqliteVec.sqlite_vec_repository import (
            SqliteVecRepository,
        )

        return SqliteVecRepository.create(path=":memory:", dimension=self.dimension)
