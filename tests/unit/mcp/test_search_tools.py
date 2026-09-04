from __future__ import annotations

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.MCP.Tools.search_tools import build_search_tools
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)

from .conftest import make_env


class TestSemanticSearchTool:
    async def test_returns_scored_results(self) -> None:
        env = make_env()
        env.vector_repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.8,
                metadata={"subject": "Invoice"},
            )
        ]
        tool = next(
            t for t in build_search_tools(env.uses) if t.name == "semantic_search"
        )

        result = await tool.handler(query="unpaid invoices", limit=5, min_score=0.5)

        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.8
        assert env.embedding.calls == ["unpaid invoices"]

    async def test_results_carry_the_gmail_message_id(self) -> None:
        env = make_env()
        email = env.add_email(message_id="gmail-9")
        env.vector_repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=email.id,
                score=0.9,
                metadata={},
            )
        ]
        tool = next(
            t for t in build_search_tools(env.uses) if t.name == "semantic_search"
        )

        result = await tool.handler(query="invoice")

        [first] = result["results"]
        assert first["message_id"] == "gmail-9"
        assert first["email_id"] == str(email.id)

    async def test_message_id_null_for_uncached_email(self) -> None:
        env = make_env()
        env.vector_repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.9,
                metadata={},
            )
        ]
        tool = next(
            t for t in build_search_tools(env.uses) if t.name == "semantic_search"
        )

        result = await tool.handler(query="x")

        assert result["results"][0]["message_id"] is None

    async def test_min_score_filters_results(self) -> None:
        env = make_env()
        env.vector_repo.search_results = [
            SearchResult(
                document_id=UUIDId.generate(),
                email_id=UUIDId.generate(),
                score=0.2,
                metadata={},
            )
        ]
        tool = next(
            t for t in build_search_tools(env.uses) if t.name == "semantic_search"
        )

        result = await tool.handler(query="x", min_score=0.5)

        assert result["results"] == []
