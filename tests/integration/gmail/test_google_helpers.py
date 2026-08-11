from __future__ import annotations

import base64

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import DomainError
from agentic_mail_mcp.Gmail.Infrastructure.Google.message_parser import (
    to_gmail_message,
    to_gmail_thread,
)
from agentic_mail_mcp.Gmail.Infrastructure.Google.oauth_provider import (
    GmailOAuthProvider,
)
from agentic_mail_mcp.Gmail.Infrastructure.Google.rate_limiter import RateLimiter
from agentic_mail_mcp.Gmail.Infrastructure.Google.retry import retry_on_transient
from tests.integration.gmail.fake_gmail_service import FakeHttpError


class TestGmailOAuthProvider:
    def test_save_and_load_round_trip(self, tmp_path) -> None:
        path = tmp_path / "sub" / "token.enc"
        provider = GmailOAuthProvider(str(path), "my-secret")
        provider.save_token('{"refresh_token": "abc"}')

        assert provider.has_token()
        assert provider.load_token() == '{"refresh_token": "abc"}'
        # Stored bytes are encrypted, not plaintext.
        assert b"refresh_token" not in path.read_bytes()

    def test_wrong_key_cannot_decrypt(self, tmp_path) -> None:
        path = tmp_path / "token.enc"
        GmailOAuthProvider(str(path), "secret-a").save_token('{"x": 1}')
        with pytest.raises(DomainError):
            GmailOAuthProvider(str(path), "secret-b").load_token()

    def test_missing_token_raises(self, tmp_path) -> None:
        provider = GmailOAuthProvider(str(tmp_path / "none.enc"), "secret")
        assert provider.has_token() is False
        with pytest.raises(DomainError):
            provider.load_token()

    def test_empty_key_rejected(self, tmp_path) -> None:
        with pytest.raises(DomainError):
            GmailOAuthProvider(str(tmp_path / "t.enc"), "")


class TestRetry:
    def test_retries_then_succeeds(self) -> None:
        calls = {"n": 0}
        slept: list[float] = []

        def op() -> str:
            calls["n"] += 1
            if calls["n"] < 3:
                raise FakeHttpError(429)
            return "ok"

        result = retry_on_transient(op, max_attempts=5, sleep=slept.append)
        assert result == "ok"
        assert calls["n"] == 3
        assert len(slept) == 2

    def test_gives_up_after_max_attempts(self) -> None:
        def op() -> str:
            raise FakeHttpError(503)

        with pytest.raises(FakeHttpError):
            retry_on_transient(op, max_attempts=2, sleep=lambda _: None)

    def test_non_transient_error_not_retried(self) -> None:
        calls = {"n": 0}

        def op() -> str:
            calls["n"] += 1
            raise FakeHttpError(400)

        with pytest.raises(FakeHttpError):
            retry_on_transient(op, max_attempts=5, sleep=lambda _: None)
        assert calls["n"] == 1


class TestRateLimiter:
    def test_waits_when_calls_too_close(self) -> None:
        now = {"t": 0.0}
        slept: list[float] = []

        limiter = RateLimiter(
            max_per_second=2.0,  # min interval 0.5s
            clock=lambda: now["t"],
            sleep=slept.append,
        )
        limiter.acquire()  # first call, no wait
        limiter.acquire()  # immediately after → must wait ~0.5s
        assert slept and slept[0] == pytest.approx(0.5)

    def test_no_wait_when_spaced_out(self) -> None:
        times = iter([0.0, 10.0])
        slept: list[float] = []
        limiter = RateLimiter(
            max_per_second=2.0, clock=lambda: next(times), sleep=slept.append
        )
        limiter.acquire()
        limiter.acquire()
        assert slept == []


class TestMessageParser:
    def test_parses_multipart_with_attachment(self) -> None:
        raw = {
            "id": "m1",
            "threadId": "t1",
            "snippet": "hi",
            "labelIds": ["INBOX"],
            "payload": {
                "headers": [
                    {"name": "Subject", "value": "Report"},
                    {"name": "From", "value": "a@b.com"},
                    {"name": "To", "value": "c@d.com"},
                ],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode(b"hello body").decode()
                        },
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "report.pdf",
                        "body": {"attachmentId": "att1", "size": 2048},
                    },
                ],
            },
        }
        message = to_gmail_message(raw)
        assert message.subject == "Report"
        assert message.body == "hello body"
        assert message.to == "c@d.com"
        assert len(message.attachments) == 1
        assert message.attachments[0].file_name == "report.pdf"
        assert message.attachments[0].size_bytes == 2048

    def test_parses_nested_multipart_body_and_attachment(self) -> None:
        # multipart/mixed -> [multipart/alternative -> [text/plain, text/html], pdf]
        raw = {
            "id": "m2",
            "threadId": "t2",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [{"name": "Subject", "value": "Nested"}],
                "parts": [
                    {
                        "mimeType": "multipart/alternative",
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"deep body"
                                    ).decode()
                                },
                            },
                            {
                                "mimeType": "text/html",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"<p>deep</p>"
                                    ).decode()
                                },
                            },
                        ],
                    },
                    {
                        "mimeType": "application/pdf",
                        "filename": "deep.pdf",
                        "body": {"attachmentId": "att9", "size": 10},
                    },
                ],
            },
        }
        message = to_gmail_message(raw)
        assert message.body == "deep body"
        assert [a.file_name for a in message.attachments] == ["deep.pdf"]

    def test_forwarded_message_keeps_original_body_alongside_the_note(self) -> None:
        # multipart/mixed -> [note (text/plain), message/rfc822 -> original
        # message's own text/plain]. Gmail nests a forwarded-as-attachment
        # message this way; the forward note must not eclipse the original.
        raw = {
            "id": "m3",
            "threadId": "t3",
            "labelIds": ["INBOX"],
            "payload": {
                "mimeType": "multipart/mixed",
                "headers": [{"name": "Subject", "value": "Fwd: Report"}],
                "parts": [
                    {
                        "mimeType": "text/plain",
                        "body": {
                            "data": base64.urlsafe_b64encode(
                                b"FYI, see below"
                            ).decode()
                        },
                    },
                    {
                        "mimeType": "message/rfc822",
                        "filename": "original.eml",
                        "body": {},
                        "parts": [
                            {
                                "mimeType": "text/plain",
                                "body": {
                                    "data": base64.urlsafe_b64encode(
                                        b"This is the original email"
                                    ).decode()
                                },
                            }
                        ],
                    },
                ],
            },
        }
        message = to_gmail_message(raw)
        assert "FYI, see below" in message.body
        assert "This is the original email" in message.body


class TestGmailThreadParser:
    def test_parses_thread_with_ordered_messages(self) -> None:
        raw = {
            "id": "t1",
            "snippet": "thread snippet",
            "historyId": "123",
            "messages": [
                {
                    "id": "m1",
                    "threadId": "t1",
                    "labelIds": ["INBOX"],
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Hi"},
                            {"name": "From", "value": "a@b.com"},
                        ],
                        "body": {
                            "data": base64.urlsafe_b64encode(b"first").decode()
                        },
                    },
                },
                {
                    "id": "m2",
                    "threadId": "t1",
                    "labelIds": ["INBOX"],
                    "payload": {
                        "headers": [
                            {"name": "Subject", "value": "Re: Hi"},
                            {"name": "From", "value": "c@d.com"},
                        ],
                        "body": {
                            "data": base64.urlsafe_b64encode(b"second").decode()
                        },
                    },
                },
            ],
        }
        thread = to_gmail_thread(raw)
        assert thread.id == "t1"
        assert [m.id for m in thread.messages] == ["m1", "m2"]
        assert [m.body for m in thread.messages] == ["first", "second"]
