"""A GmailGateway that builds its real backend on first use.

The server registers its tools at startup, before the user has necessarily
authorized. This wrapper lets that happen: it satisfies the ``GmailGateway``
port immediately, and only builds the authenticated ``GmailApiGateway`` (from the
stored OAuth token) the first time a call is made. If no token is stored yet, the
call fails with a clear, actionable message instead of crashing at startup.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from src.Common.Domain.Exceptions import DomainError
from src.Gmail.Domain.Gateway.gmail_gateway import (
    DraftResult,
    GmailGateway,
    GmailHistory,
    GmailLabel,
    GmailListResponse,
    GmailMessage,
    ModifyResult,
    SentMessageResult,
    StopWatchResult,
    WatchResponse,
)
from src.Gmail.Infrastructure.Google.gmail_api_gateway import GmailApiGateway
from src.Gmail.Infrastructure.Google.oauth_provider import GmailOAuthProvider

_NOT_AUTHORIZED = (
    "Gmail is not authorized yet. Run `gmail-mcp-server auth` once to grant "
    "access and store the token, then restart the server."
)


class LazyGmailGateway(GmailGateway):
    """Defers building the authenticated Gmail gateway until first use."""

    def __init__(
        self,
        oauth_provider: GmailOAuthProvider,
        *,
        gateway_factory: Callable[
            [Any], GmailGateway
        ] = GmailApiGateway.from_credentials,
    ) -> None:
        self._oauth = oauth_provider
        self._factory = gateway_factory
        self._gateway: GmailGateway | None = None

    def _resolve(self) -> GmailGateway:
        if self._gateway is None:
            if not self._oauth.has_token():
                raise DomainError(_NOT_AUTHORIZED)
            self._gateway = self._factory(self._oauth.load_credentials())
        return self._gateway

    # --- GmailGateway delegation ---
    def list_messages(
        self, query: str, page_token: str | None, max_results: int
    ) -> GmailListResponse:
        return self._resolve().list_messages(query, page_token, max_results)

    def get_message(self, message_id: str, fmt: str) -> GmailMessage | None:
        return self._resolve().get_message(message_id, fmt)

    def get_batch_messages(self, message_ids: list[str]) -> list[GmailMessage]:
        return self._resolve().get_batch_messages(message_ids)

    def send_message(self, raw_message: str) -> SentMessageResult:
        return self._resolve().send_message(raw_message)

    def create_draft(self, raw_message: str) -> DraftResult:
        return self._resolve().create_draft(raw_message)

    def send_draft(self, draft_id: str) -> SentMessageResult:
        return self._resolve().send_draft(draft_id)

    def delete_draft(self, draft_id: str) -> None:
        return self._resolve().delete_draft(draft_id)

    def modify_message(
        self, message_id: str, add_labels: list[str], remove_labels: list[str]
    ) -> ModifyResult:
        return self._resolve().modify_message(message_id, add_labels, remove_labels)

    def trash_message(self, message_id: str) -> None:
        return self._resolve().trash_message(message_id)

    def untrash_message(self, message_id: str) -> None:
        return self._resolve().untrash_message(message_id)

    def delete_message(self, message_id: str) -> None:
        return self._resolve().delete_message(message_id)

    def list_labels(self) -> list[GmailLabel]:
        return self._resolve().list_labels()

    def watch(self, notification_url: str, webhook_token: str) -> WatchResponse:
        return self._resolve().watch(notification_url, webhook_token)

    def stop_watch(self) -> StopWatchResult:
        return self._resolve().stop_watch()

    def get_history(self, history_id: str, start_history_id: str) -> GmailHistory:
        return self._resolve().get_history(history_id, start_history_id)

    def download_attachment(self, message_id: str, attachment_id: str) -> bytes:
        return self._resolve().download_attachment(message_id, attachment_id)
