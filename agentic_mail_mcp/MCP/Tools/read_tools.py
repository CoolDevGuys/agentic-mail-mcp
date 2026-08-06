"""Read-category MCP tools wrapping the Gmail read use cases.

Each builder returns a ``ToolDefinition`` whose async handler parses its
arguments into the use case's query object, invokes the single use case, and
serializes the result. Domain errors are mapped to structured tool errors.
"""

from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from agentic_mail_mcp.Gmail.Application.Queries.queries import (
    GetEmailQuery,
    GetThreadQuery,
    ListLabelsQuery,
    ListUnreadQuery,
    SearchEmailsQuery,
)
from agentic_mail_mcp.MCP.errors import error_result
from agentic_mail_mcp.MCP.serialization import to_jsonable
from agentic_mail_mcp.MCP.ToolRegistry import READ, ToolDefinition
from agentic_mail_mcp.MCP.Tools.arguments import parse_date, parse_email_identifier
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

_READ_ERRORS = (ValidationError, NotFoundError, PermissionError)


def build_search_emails_tool(uses: McpUseCases) -> ToolDefinition:
    async def search_emails(
        query: str = "",
        from_address: str | None = None,
        to_address: str | None = None,
        subject: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        has_attachment: bool = False,
        label: str | None = None,
        unread_only: bool = False,
        page: int = 1,
        page_size: int = 25,
    ) -> dict:
        try:
            q = SearchEmailsQuery(
                query_string=query,
                from_address=from_address,
                to_address=to_address,
                subject=subject,
                date_from=parse_date(date_from),
                date_to=parse_date(date_to),
                has_attachment=has_attachment,
                label=label,
                unread_only=unread_only,
                page=page,
                page_size=page_size,
            )
            return to_jsonable(uses.search_emails.execute(q))
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="search_emails",
        description=(
            "Search the mailbox by full-text query and structured filters "
            "(sender, recipient, subject, date range, label, unread). Returns a "
            "page of email summaries."
        ),
        category=READ,
        handler=search_emails,
    )


def build_get_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def get_email(email_id: str) -> dict:
        try:
            identifier = parse_email_identifier(email_id)
            return to_jsonable(
                uses.get_email.execute(GetEmailQuery(email_id=identifier))
            )
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="get_email",
        description=(
            "Fetch a single email with its body by internal UUID (local cache) "
            "or Gmail message id (live API)."
        ),
        category=READ,
        handler=get_email,
    )


def build_get_thread_tool(uses: McpUseCases) -> ToolDefinition:
    async def get_thread(thread_id: str) -> dict:
        try:
            return to_jsonable(
                uses.get_thread.execute(GetThreadQuery(thread_id=thread_id))
            )
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="get_thread",
        description="Fetch a conversation thread and its ordered email ids.",
        category=READ,
        handler=get_thread,
    )


def build_list_unread_tool(uses: McpUseCases) -> ToolDefinition:
    async def list_unread(limit: int = 25, label: str | None = None) -> dict:
        try:
            result = uses.list_unread.execute(ListUnreadQuery(limit=limit, label=label))
            return {"emails": to_jsonable(result)}
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="list_unread",
        description="List unread emails, optionally filtered by label.",
        category=READ,
        handler=list_unread,
    )


def build_list_labels_tool(uses: McpUseCases) -> ToolDefinition:
    async def list_labels(label_type: str = "all") -> dict:
        try:
            result = uses.list_labels.execute(ListLabelsQuery(label_type=label_type))
            return {"labels": to_jsonable(result)}
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="list_labels",
        description="List Gmail labels filtered by type (system, user, or all).",
        category=READ,
        handler=list_labels,
    )


def build_read_tools(uses: McpUseCases) -> list[ToolDefinition]:
    return [
        build_search_emails_tool(uses),
        build_get_email_tool(uses),
        build_get_thread_tool(uses),
        build_list_unread_tool(uses),
        build_list_labels_tool(uses),
    ]
