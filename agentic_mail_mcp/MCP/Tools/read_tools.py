"""Read-category MCP tools wrapping the Gmail read use cases.

Each builder returns a ``ToolDefinition`` whose async handler parses its
arguments into the use case's query object, invokes the single use case, and
serializes the result. Domain errors are mapped to structured tool errors.
"""

from __future__ import annotations

from typing import Any

from agentic_mail_mcp.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from agentic_mail_mcp.Gmail.Application.DTO.dtos import EmailDTO
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

# Fields search_emails can return, keyed by their EmailDTO attribute name.
_SEARCH_FIELDS = frozenset(
    {
        "id",
        "message_id",
        "thread_id",
        "subject",
        "snippet",
        "from_address",
        "from_display_name",
        "to_addresses",
        "date_sent",
        "is_read",
        "labels",
        "body",
        "attached_messages",
    }
)
# Short aliases agents are likely to use, mapped to EmailDTO field names.
_FIELD_ALIASES = {"from": "from_address", "to": "to_addresses", "date": "date_sent"}


def _normalize_fields(fields: list[str] | None) -> frozenset[str] | None:
    """Resolve the requested fields (expanding aliases). Returns None when no
    fields were requested, meaning "return the full email"."""
    if fields is None:
        return None
    normalized: set[str] = set()
    for name in fields:
        resolved = _FIELD_ALIASES.get(name, name)
        if resolved not in _SEARCH_FIELDS:
            raise ValidationError(
                f"unknown field {name!r}; valid fields are {sorted(_SEARCH_FIELDS)}"
            )
        normalized.add(resolved)
    return frozenset(normalized)


def _project_email(email: EmailDTO, fields: frozenset[str]) -> dict:
    """Reduce an email to the requested fields, always keeping ``id``."""
    full = to_jsonable(email)
    projected: dict = {"id": full["id"]}
    for name in sorted(fields):
        if name != "id" and name in full:
            projected[name] = full[name]
    return projected


def build_search_emails_tool(uses: McpUseCases) -> ToolDefinition:
    async def search_emails(
        query: str = "",
        query_scope: str = "all",
        from_address: str | None = None,
        to_address: str | None = None,
        subject: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        has_attachment: bool = False,
        label: str | None = None,
        unread_only: bool = False,
        direction: str | None = None,
        fields: list[str] | None = None,
        seen_ids: list[str] | None = None,
        body_max_length: int | None = None,
        page: int = 1,
        page_size: int = 25,
    ) -> dict[str, Any]:
        try:
            normalized_fields = _normalize_fields(fields)
            include_body = (
                True if normalized_fields is None else "body" in normalized_fields
            )
            q = SearchEmailsQuery(
                query_string=query,
                query_scope=query_scope,
                from_address=from_address,
                to_address=to_address,
                subject=subject,
                date_from=parse_date(date_from),
                date_to=parse_date(date_to),
                has_attachment=has_attachment,
                label=label,
                unread_only=unread_only,
                direction=direction,
                include_body=include_body,
                body_max_length=body_max_length,
                seen_ids=frozenset(seen_ids or ()),
                page=page,
                page_size=page_size,
            )
            result = uses.search_emails.execute(q)
            result_dict = to_jsonable(result)
            if normalized_fields is not None:
                result_dict["emails"] = [
                    _project_email(e, normalized_fields) for e in result.emails
                ]
            return result_dict
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="search_emails",
        description=(
            "Search the mailbox by full-text query and structured filters "
            "(sender, recipient, subject, date range, label, unread, direction). "
            "Returns a page of emails plus the exact total_count of matches. By "
            "default each email includes its full body; pass `fields` to return "
            "only the fields you need (e.g. [\"subject\", \"from\", \"date\"]) to "
            "keep results small, and `body_max_length` to cap the body length. "
            "Use `direction` to restrict to received or sent mail, and `seen_ids` "
            "to exclude messages you have already seen. Restrict the free-text "
            "`query` to one field with `query_scope` (\"subject\" or \"body\"); "
            "use it when a company name also appears in unrelated mail (CI "
            "notifications, coding challenges). To match only on the subject "
            "line, set `subject` (it searches the subject only). To match an "
            "exact phrase, wrap it in double quotes in `query` (e.g. "
            "\"quarterly report\"). Each result's `id` is the Gmail message id — "
            "pass it straight to get_email or get_thread. Some senders (e.g. "
            "LinkedIn InMail) use a generic alias address with the real person "
            "only in the display name — request the `from_display_name` field."
        ),
        category=READ,
        handler=search_emails,
    )


def build_get_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def get_email(
        email_id: str, fields: list[str] | None = None
    ) -> dict[str, Any]:
        try:
            normalized_fields = _normalize_fields(fields)
            identifier = parse_email_identifier(email_id)
            email = uses.get_email.execute(GetEmailQuery(email_id=identifier))
            if normalized_fields is None:
                return to_jsonable(email)
            return _project_email(email, normalized_fields)
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="get_email",
        description=(
            "Fetch a single email with its body by Gmail message id or internal "
            "UUID. Pass `fields` (e.g. [\"subject\", \"from\", \"date\"]) to "
            "return only those fields instead of the full body. For a forwarded "
            "email, `body` holds only the forward's own note; the forwarded "
            "original(s) are in `attached_messages`, each with its own subject, "
            "sender, date, and body."
        ),
        category=READ,
        handler=get_email,
    )


def build_get_thread_tool(uses: McpUseCases) -> ToolDefinition:
    async def get_thread(thread_id: str) -> dict[str, Any]:
        try:
            return to_jsonable(
                uses.get_thread.execute(GetThreadQuery(thread_id=thread_id))
            )
        except _READ_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="get_thread",
        description=(
            "Fetch a full conversation thread from Gmail: every message in "
            "order, each with its own body, sender, recipients, and date — "
            "enough to reconstruct the whole conversation in one call."
        ),
        category=READ,
        handler=get_thread,
    )


def build_list_unread_tool(uses: McpUseCases) -> ToolDefinition:
    async def list_unread(
        limit: int = 25, label: str | None = None
    ) -> dict[str, Any]:
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
    async def list_labels(label_type: str = "all") -> dict[str, Any]:
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
