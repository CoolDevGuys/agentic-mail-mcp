from __future__ import annotations

import json
from typing import Any

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Search.Domain.Entities.search_document import SearchDocument
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)

try:
    import pysqlite3 as sqlite3  # type: ignore[import-not-found]
except ImportError:
    import sqlite3  # type: ignore[no-redef]


class SqliteVecRepository:
    """VectorSearchRepository backed by the sqlite-vec extension.

    This is the default vector backend. sqlite-vec is the maintained successor
    to sqlite-vss and satisfies the same capability. It requires a SQLite build
    with extension loading enabled. Use pysqlite3-binary in Docker images based
    on python:<version>-slim where the system SQLite lacks extension loading support.
    """

    def __init__(self, connection: Any, dimension: int) -> None:
        self._conn = connection
        self._dimension = dimension
        self._ensure_schema()

    @classmethod
    def create(
        cls, path: str = ":memory:", dimension: int = 384
    ) -> SqliteVecRepository:
        import sqlite_vec

        conn = sqlite3.connect(path)
        conn.enable_load_extension(True)
        sqlite_vec.load(conn)
        conn.enable_load_extension(False)
        return cls(conn, dimension)

    def _ensure_schema(self) -> None:
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS documents ("
            "rowid INTEGER PRIMARY KEY, document_id TEXT, "
            "email_id TEXT UNIQUE, metadata TEXT)"
        )
        self._conn.execute(
            f"CREATE VIRTUAL TABLE IF NOT EXISTS vec_documents "
            f"USING vec0(embedding float[{self._dimension}])"
        )
        self._conn.commit()

    def index(self, document: SearchDocument) -> None:
        import sqlite_vec

        self.delete(document.email_id)
        cursor = self._conn.execute(
            "INSERT INTO documents(document_id, email_id, metadata) VALUES (?, ?, ?)",
            (str(document.id), str(document.email_id), json.dumps(document.metadata)),
        )
        rowid = cursor.lastrowid
        self._conn.execute(
            "INSERT INTO vec_documents(rowid, embedding) VALUES (?, ?)",
            (rowid, sqlite_vec.serialize_float32(document.embedding)),
        )
        self._conn.commit()

    def search(
        self, query_vector: list[float], limit: int = 10, min_score: float = 0.0
    ) -> list[SearchResult]:
        import sqlite_vec

        rows = self._conn.execute(
            "SELECT d.document_id, d.email_id, d.metadata, v.distance "
            "FROM vec_documents v JOIN documents d ON d.rowid = v.rowid "
            "WHERE v.embedding MATCH ? ORDER BY v.distance LIMIT ?",
            (sqlite_vec.serialize_float32(query_vector), limit),
        ).fetchall()

        results: list[SearchResult] = []
        for document_id, email_id, metadata, distance in rows:
            score = 1.0 / (1.0 + float(distance))
            if score >= min_score:
                results.append(
                    SearchResult(
                        document_id=UUIDId.from_string(document_id),
                        email_id=UUIDId.from_string(email_id),
                        score=score,
                        metadata=json.loads(metadata),
                    )
                )
        return results

    def delete(self, email_id: UUIDId) -> None:
        row = self._conn.execute(
            "SELECT rowid FROM documents WHERE email_id = ?", (str(email_id),)
        ).fetchone()
        if row is not None:
            self._conn.execute("DELETE FROM vec_documents WHERE rowid = ?", (row[0],))
            self._conn.execute(
                "DELETE FROM documents WHERE email_id = ?", (str(email_id),)
            )
            self._conn.commit()

    def count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
