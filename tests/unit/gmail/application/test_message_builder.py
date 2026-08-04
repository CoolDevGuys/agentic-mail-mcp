from __future__ import annotations

import base64
from email import message_from_bytes
from email.message import Message

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Application.Commands.commands import (
    CreateDraftCommand,
    ForwardEmailCommand,
)
from src.Gmail.Application.UseCases.message_builder import (
    build_draft_message,
    build_forward_message,
)
from src.Gmail.Domain.Entities.email import Email


def _decode(raw: str) -> Message:
    return message_from_bytes(base64.urlsafe_b64decode(raw.encode("ascii")))


def _original() -> Email:
    return Email.from_gmail_message(
        message_id="m1",
        thread_id="t1",
        subject="Original subject",
        from_address="sender@example.com",
        body="Original body text",
    )


class TestBuildForwardMessage:
    def test_attaches_original_as_rfc822_when_include_original(self) -> None:
        raw = build_forward_message(
            _original(),
            ForwardEmailCommand(
                email_id=UUIDId.generate(),
                to_address="dest@corp.com",
                subject="Please review",
                body="See below",
            ),
        )
        parsed = _decode(raw)
        assert parsed["To"] == "dest@corp.com"
        assert parsed["Subject"] == "Please review"

        rfc822_parts = [
            p for p in parsed.walk() if p.get_content_type() == "message/rfc822"
        ]
        assert len(rfc822_parts) == 1
        attached = rfc822_parts[0].get_payload(0)
        assert attached["Subject"] == "Original subject"
        assert "Original body text" in attached.get_payload()

    def test_omits_original_when_include_original_false(self) -> None:
        raw = build_forward_message(
            _original(),
            ForwardEmailCommand(
                email_id=UUIDId.generate(),
                to_address="dest@corp.com",
                include_original=False,
            ),
        )
        parsed = _decode(raw)
        assert not any(
            p.get_content_type() == "message/rfc822" for p in parsed.walk()
        )

    def test_defaults_subject_to_fwd_prefix(self) -> None:
        raw = build_forward_message(
            _original(),
            ForwardEmailCommand(email_id=UUIDId.generate(), to_address="d@corp.com"),
        )
        assert _decode(raw)["Subject"] == "Fwd: Original subject"


class TestBuildDraftMessage:
    def test_builds_draft_with_headers_and_body(self) -> None:
        raw = build_draft_message(
            CreateDraftCommand(to_address="a@b.com", subject="Hi", body="Draft body")
        )
        parsed = _decode(raw)
        assert parsed["To"] == "a@b.com"
        assert parsed["Subject"] == "Hi"
        assert "Draft body" in parsed.get_payload()
