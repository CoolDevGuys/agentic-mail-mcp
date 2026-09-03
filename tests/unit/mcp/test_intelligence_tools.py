from __future__ import annotations

import json
from datetime import UTC, datetime
from uuid import uuid4

from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.MCP.errors import INVALID_INPUT, NOT_FOUND
from agentic_mail_mcp.MCP.Tools.intelligence_tools import build_intelligence_tools

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

    async def test_resolves_by_gmail_message_id(self) -> None:
        env = make_env(llm_text="A short summary.")
        env.add_email(message_id="msg-123")
        tool = _tool(env.uses, "summarize_email")

        result = await tool.handler(email_id="msg-123")

        assert result["summary_text"] == "A short summary."

    async def test_unknown_message_id_maps_to_not_found(self) -> None:
        env = make_env()
        tool = _tool(env.uses, "summarize_email")

        result = await tool.handler(email_id="not-a-uuid")

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
    def _unread_on(self, env, day: datetime) -> None:
        env.email_repo.add(
            Email.from_gmail_message(
                message_id=f"m-{day.date()}",
                thread_id="t1",
                subject="Dated mail",
                date_sent=day,
                labels=["INBOX", "UNREAD"],
            )
        )

    async def test_daily_digest_runs_for_current_day(self) -> None:
        env = make_env(llm_text="Daily digest text.")
        tool = _tool(env.uses, "daily_digest")

        result = await tool.handler()

        assert result["digest_type"] == "daily"

    async def test_daily_digest_anchors_on_provided_date(self) -> None:
        env = make_env(llm_text="Daily digest text.")
        self._unread_on(env, datetime(2026, 7, 1, 10, tzinfo=UTC))
        tool = _tool(env.uses, "daily_digest")

        on_day = await tool.handler(date="2026-07-01")
        off_day = await tool.handler(date="2026-07-02")

        assert on_day["digest_period"] == "2026-07-01"
        assert on_day["email_count"] == 1
        assert off_day["email_count"] == 0

    async def test_daily_digest_rejects_malformed_date(self) -> None:
        env = make_env(llm_text="x")
        tool = _tool(env.uses, "daily_digest")

        result = await tool.handler(date="07-01-2026")

        assert result["error"]["type"] == INVALID_INPUT

    async def test_weekly_digest_anchors_on_provided_week(self) -> None:
        env = make_env(llm_text="Weekly digest text.")
        # 2026-07-01 is a Wednesday; the week runs Mon 2026-06-29 .. Sun 2026-07-05.
        self._unread_on(env, datetime(2026, 7, 1, 10, tzinfo=UTC))
        tool = _tool(env.uses, "weekly_digest")

        result = await tool.handler(week_start="2026-07-01")

        assert result["digest_type"] == "weekly"
        assert result["digest_period"] == "2026-06-29/2026-07-05"
        assert result["email_count"] == 1
