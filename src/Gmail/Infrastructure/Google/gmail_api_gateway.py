from __future__ import annotations

import base64
import time
from collections.abc import Callable
from typing import Any

from src.Gmail.Domain.Gateway.gmail_gateway import (
    DraftResult,
    GmailHistory,
    GmailLabel,
    GmailListResponse,
    GmailMessage,
    GmailMessageHeader,
    ModifyResult,
    SentMessageResult,
    StopWatchResult,
    WatchResponse,
)
from src.Gmail.Infrastructure.Google.message_parser import (
    to_gmail_message,
    to_gmail_message_header,
)
from src.Gmail.Infrastructure.Google.rate_limiter import RateLimiter
from src.Gmail.Infrastructure.Google.retry import retry_on_transient

_USER = "me"


def _status_of(error: Exception) -> int | None:
    resp = getattr(error, "resp", None)
    status = getattr(resp, "status", None)
    try:
        return int(status) if status is not None else None
    except (TypeError, ValueError):
        return None


class GmailApiGateway:
    """GmailGateway implementation over the Gmail API discovery client.

    The ``service`` (a googleapiclient resource) is injected so the mapping and
    retry/rate-limit behavior are testable without a network. Every call is
    rate-limited and retried on transient errors.
    """

    def __init__(
        self,
        service: Any,
        *,
        rate_limiter: RateLimiter | None = None,
        max_attempts: int = 3,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._service = service
        self._rate_limiter = rate_limiter
        self._max_attempts = max_attempts
        self._sleep = sleep

    @classmethod
    def from_credentials(cls, credentials: Any, **kwargs: Any) -> GmailApiGateway:  # pragma: no cover - requires google auth
        from googleapiclient.discovery import build

        service = build("gmail", "v1", credentials=credentials, cache_discovery=False)
        return cls(service, **kwargs)

    def _execute(self, request: Any) -> Any:
        if self._rate_limiter is not None:
            self._rate_limiter.acquire()
        return retry_on_transient(
            request.execute,
            max_attempts=self._max_attempts,
            sleep=self._sleep,
        )

    def _messages(self) -> Any:
        return self._service.users().messages()

    def _drafts(self) -> Any:
        return self._service.users().drafts()

    def list_messages(
        self, query: str, page_token: str | None, max_results: int
    ) -> GmailListResponse:
        result = self._execute(
            self._messages().list(
                userId=_USER, q=query, pageToken=page_token, maxResults=max_results
            )
        )
        headers = [to_gmail_message_header(m) for m in result.get("messages", [])]
        return GmailListResponse(
            messages=headers,
            next_page_token=result.get("nextPageToken"),
            result_size_estimate=int(result.get("resultSizeEstimate", 0)),
        )

    def get_message(self, message_id: str, fmt: str) -> GmailMessage | None:
        try:
            raw = self._execute(
                self._messages().get(userId=_USER, id=message_id, format=fmt)
            )
        except Exception as error:
            if _status_of(error) == 404:
                return None
            raise
        return to_gmail_message(raw)

    def get_batch_messages(self, message_ids: list[str]) -> list[GmailMessage]:
        messages: list[GmailMessage] = []
        for message_id in message_ids:
            message = self.get_message(message_id, "full")
            if message is not None:
                messages.append(message)
        return messages

    def send_message(self, raw_message: str) -> SentMessageResult:
        result = self._execute(
            self._messages().send(userId=_USER, body={"raw": raw_message})
        )
        return SentMessageResult(
            message_id=result.get("id", ""), thread_id=result.get("threadId", "")
        )

    def create_draft(self, raw_message: str) -> DraftResult:
        result = self._execute(
            self._drafts().create(
                userId=_USER, body={"message": {"raw": raw_message}}
            )
        )
        message = result.get("message", {})
        return DraftResult(
            draft_id=result.get("id", ""), message_id=message.get("id", "")
        )

    def send_draft(self, draft_id: str) -> SentMessageResult:
        result = self._execute(
            self._drafts().send(userId=_USER, body={"id": draft_id})
        )
        return SentMessageResult(
            message_id=result.get("id", ""), thread_id=result.get("threadId", "")
        )

    def delete_draft(self, draft_id: str) -> None:
        self._execute(self._drafts().delete(userId=_USER, id=draft_id))

    def modify_message(
        self, message_id: str, add_labels: list[str], remove_labels: list[str]
    ) -> ModifyResult:
        result = self._execute(
            self._messages().modify(
                userId=_USER,
                id=message_id,
                body={"addLabelIds": add_labels, "removeLabelIds": remove_labels},
            )
        )
        return ModifyResult(label_ids=list(result.get("labelIds", [])))

    def trash_message(self, message_id: str) -> None:
        self._execute(self._messages().trash(userId=_USER, id=message_id))

    def untrash_message(self, message_id: str) -> None:
        self._execute(self._messages().untrash(userId=_USER, id=message_id))

    def delete_message(self, message_id: str) -> None:
        self._execute(self._messages().delete(userId=_USER, id=message_id))

    def list_labels(self) -> list[GmailLabel]:
        result = self._execute(self._service.users().labels().list(userId=_USER))
        return [
            GmailLabel(
                id=label.get("id", ""),
                name=label.get("name", ""),
                type=label.get("type", "user"),
                color=label.get("color"),
            )
            for label in result.get("labels", [])
        ]

    def watch(self, notification_url: str, webhook_token: str) -> WatchResponse:
        result = self._execute(
            self._service.users().watch(
                userId=_USER,
                body={"topicName": notification_url, "token": webhook_token},
            )
        )
        return WatchResponse(expiration=int(result.get("expiration", 0)))

    def stop_watch(self) -> StopWatchResult:
        self._execute(self._service.users().stop(userId=_USER))
        return StopWatchResult(success=True)

    def get_history(self, history_id: str, start_history_id: str) -> GmailHistory:
        result = self._execute(
            self._service.users().history().list(
                userId=_USER, startHistoryId=start_history_id
            )
        )
        messages: list[GmailMessageHeader] = []
        for entry in result.get("history", []):
            for added in entry.get("messagesAdded", []):
                messages.append(to_gmail_message_header(added.get("message", {})))
        return GmailHistory(
            history_id=str(result.get("historyId", history_id)),
            messages=messages,
            labels=[],
        )

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        result = self._execute(
            self._messages()
            .attachments()
            .get(userId=_USER, messageId=message_id, id=attachment_id)
        )
        data = result.get("data", "")
        padded = data + "=" * (-len(data) % 4)
        return base64.urlsafe_b64decode(padded)
