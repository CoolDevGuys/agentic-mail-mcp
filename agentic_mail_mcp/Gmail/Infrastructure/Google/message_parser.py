from __future__ import annotations

import base64
from collections.abc import Iterator
from typing import Any

from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailAttachment,
    GmailMessage,
    GmailMessageHeader,
)


def _walk_leaf_parts(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield every leaf part, recursing through nested multipart containers.

    Gmail nests ``text/plain`` inside ``multipart/alternative`` and attachments
    inside ``multipart/mixed`` subtrees, so a single-level scan misses them.
    """
    parts = payload.get("parts")
    if not parts:
        yield payload
        return
    for part in parts:
        yield from _walk_leaf_parts(part)


def _header(headers: list[dict[str, Any]], name: str) -> str:
    for header in headers:
        if header.get("name", "").lower() == name.lower():
            return header.get("value", "")
    return ""


def _decode_b64url(data: str) -> str:
    if not data:
        return ""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded).decode("utf-8", errors="replace")


def _extract_body(payload: dict[str, Any]) -> str:
    first_data: str | None = None
    for part in _walk_leaf_parts(payload):
        data = part.get("body", {}).get("data")
        if not data:
            continue
        if part.get("mimeType") == "text/plain":
            return _decode_b64url(data)
        if first_data is None:
            first_data = _decode_b64url(data)
    return first_data or ""


def _extract_attachments(payload: dict[str, Any]) -> list[GmailAttachment]:
    attachments: list[GmailAttachment] = []
    for part in _walk_leaf_parts(payload):
        filename = part.get("filename")
        body = part.get("body", {})
        if filename and body.get("attachmentId"):
            attachments.append(
                GmailAttachment(
                    id=body["attachmentId"],
                    file_name=filename,
                    mime_type=part.get("mimeType", ""),
                    size_bytes=int(body.get("size", 0)),
                )
            )
    return attachments


def to_gmail_message(raw: dict[str, Any]) -> GmailMessage:
    payload = raw.get("payload", {})
    headers = payload.get("headers", [])
    return GmailMessage(
        id=raw.get("id", ""),
        thread_id=raw.get("threadId", ""),
        snippet=raw.get("snippet", ""),
        subject=_header(headers, "Subject"),
        from_=_header(headers, "From"),
        to=_header(headers, "To"),
        date=_header(headers, "Date"),
        labels=list(raw.get("labelIds", [])),
        body=_extract_body(payload),
        attachments=_extract_attachments(payload),
    )


def to_gmail_message_header(raw: dict[str, Any]) -> GmailMessageHeader:
    payload = raw.get("payload", {})
    headers = payload.get("headers", [])
    return GmailMessageHeader(
        id=raw.get("id", ""),
        thread_id=raw.get("threadId", ""),
        snippet=raw.get("snippet", ""),
        subject=_header(headers, "Subject"),
        from_=_header(headers, "From"),
        date=_header(headers, "Date"),
        labels=list(raw.get("labelIds", [])),
    )
