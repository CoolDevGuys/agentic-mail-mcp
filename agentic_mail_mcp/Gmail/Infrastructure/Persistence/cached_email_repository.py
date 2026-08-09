"""Read-through email cache over the live Gmail gateway.

Gmail is the source of truth; this repository is a thin accelerator, never a
mirror:

- **Single-email reads** (`find_by_gmail_message_id`, `find_by_id`) always go to
  the gateway so the caller gets fresh, complete data (including the body). The
  result is upserted into the SQLite cache **metadata-only** — the body is never
  written at rest — with a stable UUID keyed by the Gmail message id.
- **List reads** (`list_unread`, `find_by_thread_id`, `search`) are served from
  the metadata cache, filtered by a short **TTL** so stale rows are ignored.
- A message that the gateway reports as gone (404 / ``None``) is **evicted** from
  the cache and reported as not found. No delete-propagation job, no history sync.
"""

from __future__ import annotations

from datetime import timedelta

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Common.Infrastructure.Clock import Clock, SystemClock
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Mapper.email_mapper import EmailMapper
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository


class CachedEmailRepository(EmailRepository):
    def __init__(
        self,
        cache: EmailRepository,
        gateway: GmailGateway,
        *,
        clock: Clock | None = None,
        ttl_seconds: int = 900,
    ) -> None:
        self._cache = cache
        self._gateway = gateway
        self._clock = clock or SystemClock()
        self._ttl = timedelta(seconds=ttl_seconds)
        # In-memory freshness map keyed by Gmail message id. Seeded from the
        # persisted cache on init so cached entries remain usable after restart.
        self._seen_at: dict[str, object] = {}
        self._seed_seen_at()

    def _seed_seen_at(self) -> None:
        now = self._clock.now()
        for email in self._cache.list_all():
            self._seen_at[email.message_id.value] = now

    # --- single-email reads: live-through, metadata-only cache ---

    def find_by_gmail_message_id(self, message_id: str) -> Email | None:
        message = self._gateway.get_message(message_id, "full")
        if message is None:
            self._evict(message_id)
            return None
        return self._absorb(EmailMapper.to_domain(message))

    def find_by_id(self, id: UUIDId) -> Email | None:
        cached = self._cache.find_by_id(id)
        if cached is None:
            return None
        # Re-resolve live by the mapped Gmail message id for a fresh, full email.
        return self.find_by_gmail_message_id(cached.message_id.value)

    # --- list reads: cache, TTL-filtered ---

    def find_by_thread_id(self, thread_id: str) -> list[Email]:
        return [e for e in self._cache.find_by_thread_id(thread_id) if self._fresh(e)]

    def list_unread(self, limit: int) -> list[Email]:
        fresh = [e for e in self._cache.list_unread(limit) if self._fresh(e)]
        return fresh[:limit]

    def search(self, query: str) -> list[Email]:
        return [e for e in self._cache.search(query) if self._fresh(e)]

    def list_all(self) -> list[Email]:
        return [e for e in self._cache.list_all() if self._fresh(e)]

    # --- writes ---

    def save(self, email: Email) -> None:
        self._absorb(email)

    def delete(self, id: UUIDId) -> None:
        cached = self._cache.find_by_id(id)
        if cached is not None:
            self._seen_at.pop(cached.message_id.value, None)
        self._cache.delete(id)

    # --- internals ---

    def _absorb(self, email: Email) -> Email:
        """Cache ``email`` metadata-only (body stripped) with a stable UUID, and
        return the full email untouched."""
        message_id = email.message_id.value
        existing = self._cache.find_by_gmail_message_id(message_id)
        cache_id = existing.id if existing is not None else email.id

        metadata = EmailMapper.to_domain(
            self._to_gateway_stub(email)
        )  # rebuilds without a body
        metadata.id = cache_id
        self._cache.save(metadata)
        self._seen_at[message_id] = self._clock.now()

        email.id = cache_id
        return email

    def _to_gateway_stub(self, email: Email):
        from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailMessage

        return GmailMessage(
            id=email.message_id.value,
            thread_id=email.thread_id.value,
            snippet=email.snippet,
            subject=email.subject,
            from_=email.from_address.value if email.from_address else "",
            to=",".join(a.value for a in email.to_addresses),
            date=email.date_sent.isoformat() if email.date_sent else "",
            labels=list(email.labels),
            body="",  # metadata-only: never persist the body at rest
            attachments=[],
        )

    def _fresh(self, email: Email) -> bool:
        seen = self._seen_at.get(email.message_id.value)
        if seen is None:
            return False
        return self._clock.now() - seen < self._ttl  # type: ignore[operator]

    def _evict(self, message_id: str) -> None:
        self._seen_at.pop(message_id, None)
        existing = self._cache.find_by_gmail_message_id(message_id)
        if existing is not None:
            self._cache.delete(existing.id)
