from __future__ import annotations

import os

import pytest

from tests.integration.search.vector_contract import (
    VectorSearchRepositoryContractTests,
)

_PG_DSN = os.environ.get("AGENTIC_MAIL_MCP_TEST_PG_DSN")

pytestmark = pytest.mark.skipif(
    _PG_DSN is None,
    reason="PostgreSQL not available; set AGENTIC_MAIL_MCP_TEST_PG_DSN to run pgvector tests",
)


class TestPgVectorRepository(VectorSearchRepositoryContractTests):
    @pytest.fixture
    def vector_repo(self):
        pytest.importorskip("pgvector")
        pytest.importorskip("psycopg2")
        from agentic_mail_mcp.Search.Infrastructure.PgVector.pgvector_repository import (
            PgVectorRepository,
        )

        repo = PgVectorRepository.create(_PG_DSN, dimension=self.dimension)
        # Clean slate for a deterministic run.
        with repo._conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS search_documents")
        repo._ensure_schema()
        return repo
