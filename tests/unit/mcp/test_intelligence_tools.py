from __future__ import annotations

import json
from uuid import uuid4

from src.MCP.errors import NOT_FOUND
from src.MCP.Tools.intelligence_tools import build_intelligence_tools

from .conftest import make_env


def _tool(uses, name):
    return next(t for t in build_intelligence_tools(uses) if t.name == name)


class TestSummarizeEmailTool:
    async def test_summarizes_via_llm(self) -> None:
        env = make_env(llm_text="A short summary.")
        email = env.add_email()
        tool = _tool(env.uses, "summarize_email")

        result = await tool.handler(email_id=str(email.id))

        assert result["summary_text"] == "A short summary."
        assert env.llm.calls  # the LLM gateway was invoked

    async def test_missing_email_maps_to_not_found(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "summarize_email")

        result = await tool.handler(email_id=str(uuid4()))

        assert result["error"]["type"] == NOT_FOUND


class TestClassifyEmailTool:
    async def test_classifies_via_llm(self) -> None:
        payload = json.dumps({"category": "urgent", "priority": 5, "confidence": 0.9})
        env = make_env(llm_text=payload)
        email = env.add_email()
        tool = _tool(env.uses, "classify_email")

        result = await tool.handler(email_id=str(email.id))

        assert result["category"] == "urgent"
        assert result["priority"] == 5


class TestSuggestReplyTool:
    async def test_suggests_reply(self) -> None:
        env = make_env(llm_text="Sure, sounds good.")
        email = env.add_email()
        tool = _tool(env.uses, "suggest_reply")

        result = await tool.handler(email_id=str(email.id))

        assert result["draft_text"] == "Sure, sounds good."
        assert result["suggestion_type"] == "reply"


class TestExtractActionItemsTool:
    async def test_extracts_items(self) -> None:
        payload = json.dumps([{"description": "Send report", "priority": 2}])
        env = make_env(llm_text=payload)
        email = env.add_email()
        tool = _tool(env.uses, "extract_action_items")

        result = await tool.handler(email_id=str(email.id))

        assert result["action_items"][0]["description"] == "Send report"


class TestDigestTools:
    async def test_daily_digest_runs(self) -> None:
        env = make_env(llm_text="Daily digest text.")
        tool = _tool(env.uses, "daily_digest")

        result = await tool.handler()

        assert result["digest_type"] == "daily"

    async def test_weekly_digest_runs(self) -> None:
        env = make_env(llm_text="Weekly digest text.")
        tool = _tool(env.uses, "weekly_digest")

        result = await tool.handler()

        assert result["digest_type"] == "weekly"
