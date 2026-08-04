"""Intelligence-category MCP tools wrapping the LLM-backed use cases."""

from __future__ import annotations

from uuid import UUID

from src.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.MCP.errors import error_result
from src.MCP.serialization import to_jsonable
from src.MCP.ToolRegistry import INTELLIGENCE, ToolDefinition
from src.MCP.Tools.use_cases import McpUseCases

_INTEL_ERRORS = (ValidationError, NotFoundError, PermissionError)


def _uuid(email_id: str) -> UUIDId:
    return UUIDId(UUID(email_id))


def build_summarize_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def summarize_email(email_id: str) -> dict:
        try:
            return to_jsonable(uses.summarize_email.execute(_uuid(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="summarize_email",
        description="Generate a concise summary of an email.",
        category=INTELLIGENCE,
        handler=summarize_email,
    )


def build_classify_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def classify_email(email_id: str) -> dict:
        try:
            return to_jsonable(uses.classify_email.execute(_uuid(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="classify_email",
        description=(
            "Classify an email into a category (urgent/normal/spam/promo) with a "
            "priority and confidence."
        ),
        category=INTELLIGENCE,
        handler=classify_email,
    )


def build_suggest_reply_tool(uses: McpUseCases) -> ToolDefinition:
    async def suggest_reply(email_id: str) -> dict:
        try:
            return to_jsonable(uses.suggest_reply.execute(_uuid(email_id)))
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="suggest_reply",
        description="Draft a suggested reply to an email.",
        category=INTELLIGENCE,
        handler=suggest_reply,
    )


def build_extract_action_items_tool(uses: McpUseCases) -> ToolDefinition:
    async def extract_action_items(email_id: str) -> dict:
        try:
            items = uses.extract_action_items.execute(_uuid(email_id))
            return {"action_items": to_jsonable(items)}
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="extract_action_items",
        description="Extract action items (description, due date, priority) from an email.",
        category=INTELLIGENCE,
        handler=extract_action_items,
    )


def build_daily_digest_tool(uses: McpUseCases) -> ToolDefinition:
    async def daily_digest(date: str | None = None) -> dict:
        # The digest window is anchored on the server clock; ``date`` is accepted
        # for forward compatibility and currently advisory.
        try:
            return to_jsonable(uses.daily_digest.execute())
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="daily_digest",
        description="Generate a digest of the day's unread/important emails.",
        category=INTELLIGENCE,
        handler=daily_digest,
    )


def build_weekly_digest_tool(uses: McpUseCases) -> ToolDefinition:
    async def weekly_digest(week_start: str | None = None) -> dict:
        try:
            return to_jsonable(uses.weekly_digest.execute())
        except _INTEL_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="weekly_digest",
        description="Generate a digest of the week's unread/important emails.",
        category=INTELLIGENCE,
        handler=weekly_digest,
    )


def build_intelligence_tools(uses: McpUseCases) -> list[ToolDefinition]:
    return [
        build_summarize_email_tool(uses),
        build_classify_email_tool(uses),
        build_suggest_reply_tool(uses),
        build_extract_action_items_tool(uses),
        build_daily_digest_tool(uses),
        build_weekly_digest_tool(uses),
    ]
