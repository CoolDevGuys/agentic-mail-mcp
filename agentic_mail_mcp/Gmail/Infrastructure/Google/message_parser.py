from __future__ import annotations

import base64
from collections.abc import Iterator
from typing import Any

from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailAttachedMessage,
    GmailAttachment,
    GmailMessage,
    GmailMessageHeader,
    GmailThread,
)


def _walk_leaf_parts(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield every leaf part, recursing through nested multipart containers.

    Gmail nests ``text/plain`` inside ``multipart/alternative`` and attachments
    inside ``multipart/mixed`` subtrees, so a single-level scan misses them.
    ``message/rfc822`` parts (a forward's original) are not descended into:
    they are extracted separately as attached messages, so the enclosing
    message's body holds only its own content.
    """
    parts = payload.get("parts")
    if not parts:
        yield payload
        return
    for part in parts:
        if part.get("mimeType") == "message/rfc822":
            continue
        yield from _walk_leaf_parts(part)


def _iter_parts(payload: dict[str, Any]) -> Iterator[dict[str, Any]]:
    """Yield every part in the tree, at every depth."""
    for part in payload.get("parts", []):
        yield part
        yield from _iter_parts(part)


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
    """Concatenate every ``text/plain`` leaf in document order.

    Plain text is preferred over HTML: when no ``text/plain`` leaf exists the
    first other body (typically ``text/html``) is returned instead. Nested
    ``message/rfc822`` parts are excluded here — they are extracted separately
    as attached messages, so the body holds only this message's own content.
    """
    plain_texts: list[str] = []
    first_data: str | None = None
    for part in _walk_leaf_parts(payload):
        data = part.get("body", {}).get("data")
        if not data or part.get("filename"):
            continue
        if part.get("mimeType") == "text/plain":
            plain_texts.append(_decode_b64url(data))
        elif first_data is None:
            first_data = _decode_b64url(data)
    if plain_texts:
        return "\n\n".join(plain_texts)
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


def _extract_attached_messages(payload: dict[str, Any]) -> list[GmailAttachedMessage]:
    """Extract nested ``message/rfc822`` parts (forwarded originals).

    A forward embeds the original message as a ``message/rfc822`` part, which
    may itself contain further nested forwards. Each one is surfaced with its
    own subject, sender, date, and body so callers can distinguish the
    forward's note from what it forwards.
    """
    attached: list[GmailAttachedMessage] = []
    for part in _iter_parts(payload):
        if part.get("mimeType") != "message/rfc822":
            continue
        headers = part.get("headers", [])
        attached.append(
            GmailAttachedMessage(
                subject=_header(headers, "Subject"),
                from_=_header(headers, "From"),
                date=_header(headers, "Date"),
                body=_extract_body(part),
            )
        )
    return attached


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
        attached_messages=_extract_attached_messages(payload),
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
        to=_header(headers, "To"),
        body=_extract_body(payload),
    )


def to_gmail_thread(raw: dict[str, Any]) -> GmailThread:
    return GmailThread(
        id=raw.get("id", ""),
        snippet=raw.get("snippet", ""),
        history_id=str(raw.get("historyId", "")),
        messages=[to_gmail_message(m) for m in raw.get("messages", [])],
    )
