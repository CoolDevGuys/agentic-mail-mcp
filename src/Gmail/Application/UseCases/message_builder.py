from __future__ import annotations

import base64
from email.message import EmailMessage

from src.Gmail.Application.Commands.commands import (
    CreateDraftCommand,
    ForwardEmailCommand,
)
from src.Gmail.Domain.Entities.email import Email


def _encode(message: EmailMessage) -> str:
    return base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")


def _original_as_message(original: Email) -> EmailMessage:
    inner = EmailMessage()
    inner["Subject"] = original.subject
    if original.from_address is not None:
        inner["From"] = original.from_address.value
    inner.set_content(original.body or "")
    return inner


def build_forward_message(original: Email, command: ForwardEmailCommand) -> str:
    """Build a base64url raw forward, optionally attaching the original as RFC822."""
    message = EmailMessage()
    message["To"] = command.to_address
    message["Subject"] = command.subject or f"Fwd: {original.subject}"
    message.set_content(command.body or "")
    if command.include_original:
        # An EmailMessage attachment is encoded as message/rfc822 automatically.
        message.add_attachment(_original_as_message(original))
    return _encode(message)


def build_draft_message(command: CreateDraftCommand) -> str:
    message = EmailMessage()
    message["To"] = command.to_address
    message["Subject"] = command.subject
    message.set_content(command.body or "")
    return _encode(message)
