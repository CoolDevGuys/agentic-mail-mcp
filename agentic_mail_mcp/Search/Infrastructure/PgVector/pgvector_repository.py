from __future__ import annotations

import json
from typing import Any

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Search.Domain.Entities.search_document import SearchDocument
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)


class PgVectorRepository:
    """VectorSearchRepository backed by the PostgreSQL pgvector extension.

    Optional backend; requires PostgreSQL with the pgvector extension and the
    ``postgresql`` extra installed. Interchangeable with SqliteVecRepository via
    the shared VectorSearchRepository contract.
    """

    def __init__(
        self, connection: Any, dimension: int, *, table: str = "search_documents"
    ) -> None:
        self._conn = connection
        self._dimension = dimension
        self._table = table
        self._ensure_schema()

    @classmethod
    def create(cls, dsn: str, dimension: int = 384) -> PgVectorRepository:
        import psycopg2
        from pgvector.psycopg2 import register_vector

        conn = psycopg2.connect(dsn)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)
        return cls(conn, dimension)

    def _ensure_schema(self) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"CREATE TABLE IF NOT EXISTS {self._table} ("
                "document_id TEXT, email_id TEXT PRIMARY KEY, "
                f"metadata JSONB, embedding vector({self._dimension}))"
            )

    def index(self, document: SearchDocument) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {self._table} "
                "(document_id, email_id, metadata, embedding) VALUES (%s, %s, %s, %s) "
                "ON CONFLICT (email_id) DO UPDATE SET "
                "document_id = EXCLUDED.document_id, metadata = EXCLUDED.metadata, "
                "embedding = EXCLUDED.embedding",
                (
                    str(document.id),
                    str(document.email_id),
                    json.dumps(document.metadata),
                    document.embedding,
                ),
            )

    def search(
        self, query_vector: list[float], limit: int = 10, min_score: float = 0.0
    ) -> list[SearchResult]:
        with self._conn.cursor() as cur:
            cur.execute(
                f"SELECT document_id, email_id, metadata, "
                "1 - (embedding <=> %s) AS score "
                f"FROM {self._table} ORDER BY embedding <=> %s LIMIT %s",
                (query_vector, query_vector, limit),
            )
            rows = cur.fetchall()

        results: list[SearchResult] = []
        for document_id, email_id, metadata, score in rows:
            if score >= min_score:
                meta = metadata if isinstance(metadata, dict) else json.loads(metadata)
                results.append(
                    SearchResult(
                        document_id=UUIDId.from_string(document_id),
                        email_id=UUIDId.from_string(email_id),
                        score=float(score),
                        metadata=meta,
                    )
                )
        return results

    def delete(self, email_id: UUIDId) -> None:
        with self._conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {self._table} WHERE email_id = %s", (str(email_id),)
            )

    def count(self) -> int:
        with self._conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM {self._table}")
            return cur.fetchone()[0]
