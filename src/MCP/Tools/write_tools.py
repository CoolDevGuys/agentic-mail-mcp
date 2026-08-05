"""Write-category MCP tools wrapping the railguarded write use cases.

These tools are only registered when the railguard access level is
``read_write`` (see ToolRegistry). Even so, each handler still maps a railguard
``PermissionError`` to a structured tool error carrying the denial reason, so a
denial surfaces cleanly instead of raising.
"""

from __future__ import annotations

from src.Common.Domain.Exceptions import (
    NotFoundError,
    PermissionError,
    ValidationError,
)
from src.Gmail.Application.Commands.commands import (
    AddLabelCommand,
    ArchiveEmailCommand,
    CreateDraftCommand,
    DeleteEmailCommand,
    ForwardEmailCommand,
    SendDraftCommand,
)
from src.MCP.errors import error_result
from src.MCP.serialization import to_jsonable
from src.MCP.ToolRegistry import WRITE, ToolDefinition
from src.MCP.Tools.arguments import parse_uuid
from src.MCP.Tools.use_cases import McpUseCases

_WRITE_ERRORS = (ValidationError, NotFoundError, PermissionError)


def build_forward_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def forward_email(
        email_id: str,
        to: str,
        subject: str = "",
        body: str = "",
        include_original: bool = True,
    ) -> dict:
        try:
            command = ForwardEmailCommand(
                email_id=parse_uuid(email_id),
                to_address=to,
                subject=subject,
                body=body,
                include_original=include_original,
            )
            return to_jsonable(uses.forward_email.execute(command))
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="forward_email",
        description=(
            "Forward an email to a recipient (subject to the railguard "
            "allowlist and rate limits). The original is attached."
        ),
        category=WRITE,
        handler=forward_email,
    )


def build_archive_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def archive_email(
        email_id: str | None = None, thread_id: str | None = None
    ) -> dict:
        try:
            command = ArchiveEmailCommand(
                email_id=parse_uuid(email_id) if email_id else None,
                thread_id=thread_id,
            )
            uses.archive_email.execute(command)
            return {"status": "archived"}
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="archive_email",
        description="Archive an email or a whole thread (removes it from the inbox).",
        category=WRITE,
        handler=archive_email,
    )


def build_delete_email_tool(uses: McpUseCases) -> ToolDefinition:
    async def delete_email(email_id: str, permanent: bool = False) -> dict:
        try:
            command = DeleteEmailCommand(
                email_id=parse_uuid(email_id), permanent=permanent
            )
            uses.delete_email.execute(command)
            return {"status": "deleted", "permanent": permanent}
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="delete_email",
        description=(
            "Delete an email. Soft-deletes to Trash by default; permanent "
            "deletion is only honored when the railguards allow it."
        ),
        category=WRITE,
        handler=delete_email,
    )


def build_create_draft_tool(uses: McpUseCases) -> ToolDefinition:
    async def create_draft(to: str, subject: str = "", body: str = "") -> dict:
        try:
            command = CreateDraftCommand(to_address=to, subject=subject, body=body)
            draft_id = uses.create_draft.execute(command)
            return {"draft_id": draft_id}
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="create_draft",
        description=(
            "Create a draft for human review without sending it. Returns the "
            "draft id to send later with send_draft."
        ),
        category=WRITE,
        handler=create_draft,
    )


def build_send_draft_tool(uses: McpUseCases) -> ToolDefinition:
    async def send_draft(draft_id: str) -> dict:
        try:
            command = SendDraftCommand(draft_id=draft_id)
            return to_jsonable(uses.send_draft.execute(command))
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="send_draft",
        description="Send a previously created, human-reviewed draft.",
        category=WRITE,
        handler=send_draft,
    )


def build_add_label_tool(uses: McpUseCases) -> ToolDefinition:
    async def add_label(email_id: str, label: str) -> dict:
        try:
            command = AddLabelCommand(email_id=parse_uuid(email_id), label_name=label)
            uses.add_label.execute(command)
            return {"status": "labeled", "label": label}
        except _WRITE_ERRORS as exc:
            return error_result(exc)

    return ToolDefinition(
        name="add_label",
        description="Add a label to an email.",
        category=WRITE,
        handler=add_label,
    )


def build_write_tools(uses: McpUseCases) -> list[ToolDefinition]:
    return [
        build_forward_email_tool(uses),
        build_archive_email_tool(uses),
        build_delete_email_tool(uses),
        build_create_draft_tool(uses),
        build_send_draft_tool(uses),
        build_add_label_tool(uses),
    ]
