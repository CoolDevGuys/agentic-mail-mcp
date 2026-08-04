from __future__ import annotations

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.MCP.Tools.search_tools import build_search_tools
from src.Search.Domain.Repository.vector_search_repository import SearchResult

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
        tool = next(t for t in build_search_tools(env.uses) if t.name == "semantic_search")

        result = await tool.handler(query="unpaid invoices", limit=5, min_score=0.5)

        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.8
        assert env.embedding.calls == ["unpaid invoices"]

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
        tool = next(t for t in build_search_tools(env.uses) if t.name == "semantic_search")

        result = await tool.handler(query="x", min_score=0.5)

        assert result["results"] == []
