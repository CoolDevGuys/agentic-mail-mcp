"""In-memory, port-conforming fakes for application-layer unit tests.

These implement the Phase 3 domain ports faithfully (synchronous signatures),
unlike the Phase 1 placeholder stubs in this package.
"""

from __future__ import annotations

from typing import Any

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Entities.thread import Thread
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    DraftResult,
    GmailLabel,
    GmailListResponse,
    GmailMessage,
    ModifyResult,
    SentMessageResult,
)
from agentic_mail_mcp.Intelligence.Domain.Gateway.llm_gateway import LlmResponse, Usage
from agentic_mail_mcp.Search.Domain.Entities.search_document import SearchDocument
from agentic_mail_mcp.Search.Domain.Repository.vector_search_repository import (
    SearchResult,
)


class InMemoryEmailRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUIDId, Email] = {}
        self.search_results: list[Email] = []

    def add(self, email: Email) -> None:
        self._by_id[email.id] = email

    def find_by_id(self, id: UUIDId) -> Email | None:
        return self._by_id.get(id)

    def find_by_gmail_message_id(self, message_id: str) -> Email | None:
        for email in self._by_id.values():
            if email.message_id.value == message_id:
                return email
        return None

    def find_by_thread_id(self, thread_id: str) -> list[Email]:
        return [e for e in self._by_id.values() if e.thread_id.value == thread_id]

    def search(self, query: str) -> list[Email]:
        return list(self.search_results)

    def list_unread(self, limit: int) -> list[Email]:
        unread = [e for e in self._by_id.values() if not e.is_read]
        return unread[:limit]

    def save(self, email: Email) -> None:
        self._by_id[email.id] = email

    def delete(self, id: UUIDId) -> None:
        self._by_id.pop(id, None)


class InMemoryThreadRepository:
    def __init__(self) -> None:
        self._by_id: dict[UUIDId, Thread] = {}
        self._by_gmail_id: dict[str, Thread] = {}

    def add(self, thread: Thread) -> None:
        self.save(thread)

    def find_by_id(self, id: UUIDId) -> Thread | None:
        return self._by_id.get(id)

    def find_by_gmail_thread_id(self, thread_id: str) -> Thread | None:
        return self._by_gmail_id.get(thread_id)

    def save(self, thread: Thread) -> None:
        self._by_id[thread.id] = thread
        self._by_gmail_id[thread.thread_id.value] = thread

    def delete(self, id: UUIDId) -> None:
        thread = self._by_id.pop(id, None)
        if thread is not None:
            self._by_gmail_id.pop(thread.thread_id.value, None)


class StubGmailGateway:
    def __init__(self) -> None:
        self.list_response = GmailListResponse(
            messages=[], next_page_token=None, result_size_estimate=0
        )
        self.messages: dict[str, GmailMessage] = {}
        self.labels: list[GmailLabel] = []
        self.list_calls: list[tuple[str, str | None, int]] = []
        self.sent: list[str] = []
        self.drafts_created: list[str] = []
        self.drafts_sent: list[str] = []
        self.drafts_deleted: list[str] = []
        self.modify_calls: list[tuple[str, list[str], list[str]]] = []
        self.trashed: list[str] = []
        self.untrashed: list[str] = []
        self.deleted: list[str] = []

    def list_messages(
        self, query: str, page_token: str | None, max_results: int
    ) -> GmailListResponse:
        self.list_calls.append((query, page_token, max_results))
        return self.list_response

    def get_message(self, message_id: str, fmt: str) -> GmailMessage | None:
        return self.messages.get(message_id)

    def list_labels(self) -> list[GmailLabel]:
        return list(self.labels)

    # --- write operations (recorded for assertions) ---
    def send_message(self, raw_message: str) -> SentMessageResult:
        self.sent.append(raw_message)
        return SentMessageResult(message_id="sent-1", thread_id="thread-1")

    def create_draft(self, raw_message: str) -> DraftResult:
        self.drafts_created.append(raw_message)
        return DraftResult(draft_id="draft-1", message_id="draft-msg-1")

    def send_draft(self, draft_id: str) -> SentMessageResult:
        self.drafts_sent.append(draft_id)
        return SentMessageResult(message_id="sent-1", thread_id="thread-1")

    def delete_draft(self, draft_id: str) -> None:
        self.drafts_deleted.append(draft_id)

    def modify_message(
        self, message_id: str, add_labels: list[str], remove_labels: list[str]
    ) -> ModifyResult:
        self.modify_calls.append((message_id, add_labels, remove_labels))
        return ModifyResult(label_ids=[])

    def trash_message(self, message_id: str) -> None:
        self.trashed.append(message_id)

    def untrash_message(self, message_id: str) -> None:
        self.untrashed.append(message_id)

    def delete_message(self, message_id: str) -> None:
        self.deleted.append(message_id)


class StubLlmGateway:
    def __init__(
        self, response_text: str = "stub summary", model: str = "stub-model"
    ) -> None:
        self.response_text = response_text
        self.model = model
        self.calls: list[dict[str, Any]] = []

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        model: str,
    ) -> LlmResponse:
        self.calls.append(
            {
                "prompt": prompt,
                "system_prompt": system_prompt,
                "max_tokens": max_tokens,
                "model": model,
            }
        )
        return LlmResponse(
            text=self.response_text,
            model=self.model,
            usage=Usage(input_tokens=10, output_tokens=20),
        )


class StubEmbeddingGateway:
    def __init__(self, dimension: int = 4) -> None:
        self._dimension = dimension
        self.calls: list[str] = []

    def embed(self, text: str) -> list[float]:
        self.calls.append(text)
        return [float((len(text) + i) % 7) for i in range(self._dimension)]

    def dimension(self) -> int:
        return self._dimension


class InMemoryVectorSearchRepository:
    def __init__(self) -> None:
        self.documents: dict[UUIDId, SearchDocument] = {}
        self.search_results: list[SearchResult] = []

    def index(self, document: SearchDocument) -> None:
        self.documents[document.email_id] = document

    def search(
        self, query_vector: list[float], limit: int = 10, min_score: float = 0.0
    ) -> list[SearchResult]:
        results = [r for r in self.search_results if r.score >= min_score]
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:limit]

    def delete(self, email_id: UUIDId) -> None:
        self.documents.pop(email_id, None)

    def count(self) -> int:
        return len(self.documents)


class InMemorySummaryRepository:
    def __init__(self) -> None:
        self.saved: list[Any] = []

    def save(self, summary: Any) -> None:
        self.saved.append(summary)


class InMemoryClassificationRepository:
    def __init__(self) -> None:
        self.saved: list[Any] = []

    def save(self, classification: Any) -> None:
        self.saved.append(classification)


class InMemorySuggestionRepository:
    def __init__(self) -> None:
        self.saved: list[Any] = []

    def save(self, suggestion: Any) -> None:
        self.saved.append(suggestion)


class InMemoryAuditLogRepository:
    def __init__(self) -> None:
        self.entries: list[Any] = []

    def save(self, entry: Any) -> None:
        self.entries.append(entry)

    def list_all(self) -> list[Any]:
        return list(self.entries)


class RecordingNotificationGateway:
    def __init__(self, send_result: bool = True, publish_result: bool = True) -> None:
        self.send_result = send_result
        self.publish_result = publish_result
        self.sent: list[dict[str, str]] = []
        self.published: list[dict[str, Any]] = []

    def send(self, title: str, body: str, channel: str) -> bool:
        self.sent.append({"title": title, "body": body, "channel": channel})
        return self.send_result

    def publish(self, event_type: str, payload: dict[str, Any]) -> bool:
        self.published.append({"event_type": event_type, "payload": payload})
        return self.publish_result
