from __future__ import annotations

from datetime import UTC, datetime, timedelta

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Gateway.gmail_gateway import GmailMessage
from src.Gmail.Infrastructure.Persistence.cached_email_repository import (
    CachedEmailRepository,
)
from tests.fakes.ports import InMemoryEmailRepository, StubGmailGateway


class _Clock:
    def __init__(self) -> None:
        self.t = datetime(2026, 8, 1, tzinfo=UTC)

    def now(self) -> datetime:
        return self.t

    def advance(self, seconds: int) -> None:
        self.t += timedelta(seconds=seconds)


def _msg(mid: str = "m1", *, labels=None, body: str = "BODY") -> GmailMessage:
    return GmailMessage(
        id=mid,
        thread_id="t1",
        snippet="hi",
        subject="Hello",
        from_="a@b.com",
        to="me@x.com",
        date="2026-08-01T10:00:00",
        labels=labels if labels is not None else ["INBOX", "UNREAD"],
        body=body,
        attachments=[],
    )


def _repo(clock=None, ttl=900):
    gw = StubGmailGateway()
    cache = InMemoryEmailRepository()
    repo = CachedEmailRepository(cache, gw, clock=clock, ttl_seconds=ttl)
    return repo, gw, cache


class TestReadThrough:
    def test_returns_full_body_but_caches_metadata_only(self) -> None:
        repo, gw, cache = _repo()
        gw.messages["m1"] = _msg(body="SECRET")

        email = repo.find_by_gmail_message_id("m1")

        assert email is not None and email.body == "SECRET"  # full to caller
        assert cache.find_by_gmail_message_id("m1").body == ""  # metadata only at rest

    def test_stable_uuid_across_reads(self) -> None:
        repo, gw, _ = _repo()
        gw.messages["m1"] = _msg()

        first = repo.find_by_gmail_message_id("m1")
        second = repo.find_by_gmail_message_id("m1")

        assert first.id == second.id

    def test_missing_message_evicts_and_returns_none(self) -> None:
        repo, gw, cache = _repo()
        gw.messages["m1"] = _msg()
        repo.find_by_gmail_message_id("m1")  # seed the cache

        del gw.messages["m1"]
        result = repo.find_by_gmail_message_id("m1")

        assert result is None
        assert cache.find_by_gmail_message_id("m1") is None  # evicted

    def test_find_by_id_resolves_live(self) -> None:
        repo, gw, _ = _repo()
        gw.messages["m1"] = _msg(body="X")
        seeded = repo.find_by_gmail_message_id("m1")

        again = repo.find_by_id(seeded.id)

        assert again is not None and again.body == "X"

    def test_find_by_id_unknown_returns_none(self) -> None:
        repo, _, _ = _repo()
        assert repo.find_by_id(UUIDId.generate()) is None


class TestTtl:
    def test_list_unread_served_within_ttl(self) -> None:
        clock = _Clock()
        repo, gw, _ = _repo(clock=clock, ttl=100)
        gw.messages["m1"] = _msg(labels=["INBOX", "UNREAD"])
        repo.find_by_gmail_message_id("m1")  # caches metadata + freshness

        assert [e.subject for e in repo.list_unread(10)] == ["Hello"]

    def test_list_unread_drops_stale_after_ttl(self) -> None:
        clock = _Clock()
        repo, gw, _ = _repo(clock=clock, ttl=100)
        gw.messages["m1"] = _msg(labels=["INBOX", "UNREAD"])
        repo.find_by_gmail_message_id("m1")

        clock.advance(101)

        assert repo.list_unread(10) == []
