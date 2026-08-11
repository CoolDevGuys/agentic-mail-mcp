from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass
class GmailAttachment:
    id: str
    file_name: str
    mime_type: str
    size_bytes: int


@dataclass
class GmailMessageHeader:
    id: str
    thread_id: str
    snippet: str
    subject: str
    from_: str
    date: str
    labels: list[str]
    to: str = ""
    body: str = ""


@dataclass
class GmailMessage:
    id: str
    thread_id: str
    snippet: str
    subject: str
    from_: str
    to: str
    date: str
    labels: list[str]
    body: str
    attachments: list[GmailAttachment]


@dataclass
class GmailListResponse:
    messages: list[GmailMessageHeader]
    next_page_token: str | None
    result_size_estimate: int


@dataclass
class GmailThread:
    id: str
    snippet: str
    history_id: str
    messages: list[GmailMessage]


@dataclass
class SentMessageResult:
    message_id: str
    thread_id: str


@dataclass
class ModifyResult:
    label_ids: list[str]


@dataclass
class DraftResult:
    draft_id: str
    message_id: str


@dataclass
class WatchResponse:
    expiration: int


@dataclass
class StopWatchResult:
    success: bool


@dataclass
class GmailLabel:
    id: str
    name: str
    type: str
    color: str | None


@dataclass
class GmailHistory:
    history_id: str
    messages: list[GmailMessageHeader]
    labels: list[GmailLabel]


@runtime_checkable
class GmailGateway(Protocol):
    def list_messages(
        self,
        query: str,
        page_token: str | None,
        max_results: int,
    ) -> GmailListResponse: ...

    def batch_get_metadata(
        self,
        message_ids: list[str],
    ) -> list[GmailMessageHeader]: ...

    def get_message(self, message_id: str, fmt: str) -> GmailMessage | None: ...

    def get_batch_messages(self, message_ids: list[str]) -> list[GmailMessage]: ...

    def get_thread(self, thread_id: str) -> GmailThread | None: ...

    def send_message(self, raw_message: str) -> SentMessageResult: ...

    def create_draft(self, raw_message: str) -> DraftResult: ...

    def send_draft(self, draft_id: str) -> SentMessageResult: ...

    def delete_draft(self, draft_id: str) -> None: ...

    def modify_message(
        self,
        message_id: str,
        add_labels: list[str],
        remove_labels: list[str],
    ) -> ModifyResult: ...

    def trash_message(self, message_id: str) -> None: ...

    def untrash_message(self, message_id: str) -> None: ...

    def delete_message(self, message_id: str) -> None: ...

    def list_labels(self) -> list[GmailLabel]: ...

    def get_profile(self) -> str: ...

    def watch(
        self,
        notification_url: str,
        webhook_token: str,
    ) -> WatchResponse: ...

    def stop_watch(self) -> StopWatchResult: ...

    def get_history(
        self,
        history_id: str,
        start_history_id: str,
    ) -> GmailHistory: ...

    def download_attachment(
        self,
        message_id: str,
        attachment_id: str,
    ) -> bytes: ...
