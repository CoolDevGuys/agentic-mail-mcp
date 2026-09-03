"""Intelligence-category MCP tools wrapping the LLM-backed use cases.

Caller-first by default: per-email reasoning is exposed as MCP *prompts* the
calling agent runs (see ``Prompts.py``), not as internal-inference tools. A tool
is only built when its backing use case has actually been wired by the
composition root — per-email tools require ``llm.internal_tools=true``, digests
require a configured LLM. Unwired use cases are ``None`` and simply skipped.
"""

from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from agentic_mail_mcp.MCP.errors import error_result
from agentic_mail_mcp.MCP.serialization import to_jsonable
from agentic_mail_mcp.MCP.ToolRegistry import INTELLIGENCE, ToolDefinition
from agentic_mail_mcp.MCP.Tools.arguments import (
    parse_date_anchor,
    parse_email_identifier,
)
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

_INTEL_ERRORS = (ValidationError, NotFoundError, PermissionError)


def build_summarize_email_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.summarize_email
    assert use_case is not None

    async def summarize_email(email_id: str) -> dict:
        try:
            return to_jsonable(use_case.execute(parse_email_identifier(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="summarize_email",
        description=(
            "Generate a concise summary of an email. email_id is the Gmail "
            "message id (or cache UUID)."
        ),
        category=INTELLIGENCE,
        handler=summarize_email,
    )


def build_classify_email_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.classify_email
    assert use_case is not None

    async def classify_email(email_id: str) -> dict:
        try:
            return to_jsonable(use_case.execute(parse_email_identifier(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="classify_email",
        description=(
            "Classify an email into a category (urgent/normal/spam/promo) with a "
            "priority and confidence. email_id is the Gmail message id (or cache "
            "UUID)."
        ),
        category=INTELLIGENCE,
        handler=classify_email,
    )


def build_suggest_reply_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.suggest_reply
    assert use_case is not None

    async def suggest_reply(email_id: str) -> dict:
        try:
            return to_jsonable(use_case.execute(parse_email_identifier(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="suggest_reply",
        description=(
            "Draft a suggested reply to an email. email_id is the Gmail message "
            "id (or cache UUID)."
        ),
        category=INTELLIGENCE,
        handler=suggest_reply,
    )


def build_extract_action_items_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.extract_action_items
    assert use_case is not None

    async def extract_action_items(email_id: str) -> dict:
        try:
            items = use_case.execute(parse_email_identifier(email_id))
            return {"action_items": to_jsonable(items)}
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="extract_action_items",
        description=(
            "Extract action items (description, due date, priority) from an "
            "email. email_id is the Gmail message id (or cache UUID)."
        ),
        category=INTELLIGENCE,
        handler=extract_action_items,
    )


def build_daily_digest_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.daily_digest
    assert use_case is not None

    async def daily_digest(date: str | None = None) -> dict:
        # ``date`` (YYYY-MM-DD) selects the day to summarize; the server clock's
        # current day is used when omitted.
        try:
            return to_jsonable(use_case.execute(parse_date_anchor(date)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="daily_digest",
        description=(
            "Generate a digest of a day's unread/important emails. Pass a "
            "YYYY-MM-DD date to pick the day; defaults to today."
        ),
        category=INTELLIGENCE,
        handler=daily_digest,
    )


def build_weekly_digest_tool(uses: McpUseCases) -> ToolDefinition:
    use_case = uses.weekly_digest
    assert use_case is not None

    async def weekly_digest(week_start: str | None = None) -> dict:
        # ``week_start`` (YYYY-MM-DD) selects any date within the target week; the
        # current week is used when omitted.
        try:
            return to_jsonable(use_case.execute(parse_date_anchor(week_start)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="weekly_digest",
        description=(
            "Generate a digest of a week's unread/important emails. Pass a "
            "YYYY-MM-DD date within the target week; defaults to this week."
        ),
        category=INTELLIGENCE,
        handler=weekly_digest,
    )


def build_intelligence_tools(uses: McpUseCases) -> list[ToolDefinition]:
    tools: list[ToolDefinition] = []
    if uses.summarize_email is not None:
        tools.append(build_summarize_email_tool(uses))
    if uses.classify_email is not None:
        tools.append(build_classify_email_tool(uses))
    if uses.suggest_reply is not None:
        tools.append(build_suggest_reply_tool(uses))
    if uses.extract_action_items is not None:
        tools.append(build_extract_action_items_tool(uses))
    if uses.daily_digest is not None:
        tools.append(build_daily_digest_tool(uses))
    if uses.weekly_digest is not None:
        tools.append(build_weekly_digest_tool(uses))
    return tools
