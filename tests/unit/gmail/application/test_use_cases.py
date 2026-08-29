from __future__ import annotations

from datetime import UTC, datetime

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Application.DTO.dtos import EmailDTO, LabelDTO, ThreadDTO
from agentic_mail_mcp.Gmail.Application.Queries.queries import (
    GetEmailQuery,
    GetThreadQuery,
    ListLabelsQuery,
    ListUnreadQuery,
    SearchEmailsQuery,
)
from agentic_mail_mcp.Gmail.Application.UseCases.get_email import GetEmailUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.get_thread import GetThreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_labels import ListLabelsUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_unread import ListUnreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.search_emails import (
    SearchEmailsUseCase,
    build_gmail_query,
)
from agentic_mail_mcp.Gmail.Domain.Entities.email import Email
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import (
    GmailLabel,
    GmailMessage,
    GmailMessageHeader,
    GmailThread,
)
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId
from tests.fakes.ports import InMemoryEmailRepository, StubGmailGateway


def _make_email(message_id: str = "msg_1", *, read: bool = False, labels=None) -> Email:
    email = Email.from_gmail_message(
        message_id=message_id,
        thread_id="thread_1",
        subject="Hello",
        from_address="sender@example.com",
        to_addresses=["r@example.com"],
        body="Body text",
        labels=labels or [],
    )
    if read:
        email.mark_read()
    return email


class TestBuildGmailQuery:
    def test_combines_criteria(self) -> None:
        q = build_gmail_query(
            SearchEmailsQuery(query_string="hi", from_address="a@b.com", subject="inv")
        )
        assert (
            "hi" in q.value and "from:a@b.com" in q.value and "subject:inv" in q.value
        )

    def test_defaults_to_inbox_when_empty(self) -> None:
        assert build_gmail_query(SearchEmailsQuery()).value == "in:inbox"

    def test_flags_and_dates(self) -> None:
        from datetime import date

        q = build_gmail_query(
            SearchEmailsQuery(
                has_attachment=True,
                unread_only=True,
                label="Work",
                to_address="t@x.com",
                date_from=date(2026, 1, 1),
                date_to=date(2026, 2, 1),
            )
        )
        assert "has:attachment" in q.value
        assert "is:unread" in q.value
        assert "label:Work" in q.value
        assert "to:t@x.com" in q.value
        assert "after:2026-01-01" in q.value
        assert "before:2026-02-01" in q.value

    def test_direction_sent(self) -> None:
        q = build_gmail_query(SearchEmailsQuery(query_string="hi", direction="sent"))
        assert "in:sent" in q.value

    def test_direction_received_excludes_sent_mail(self) -> None:
        q = build_gmail_query(
            SearchEmailsQuery(query_string="hi", direction="received")
        )
        assert "-in:sent" in q.value
        assert "-in:draft" in q.value
        assert "-in:spam" in q.value
        assert "-in:trash" in q.value
        assert "-in:chats" in q.value


def _header(mid: str, *, body: str = "") -> GmailMessageHeader:
    return GmailMessageHeader(
        id=mid,
        thread_id="t1",
        snippet="snip",
        subject="Sub",
        from_="a@b.com",
        date="2026-01-01",
        labels=["INBOX"],
        body=body,
    )


class TestSearchEmailsUseCase:
    def test_live_returns_dtos_and_exact_count(self) -> None:
        gateway = StubGmailGateway()
        gateway.message_ids = ["m1"]
        gateway.headers["m1"] = _header("m1")
        uc = SearchEmailsUseCase(gateway, InMemoryEmailRepository())
        result = uc.execute(SearchEmailsQuery(query_string="hi", page_size=5))

        assert len(result.emails) == 1
        assert result.emails[0].message_id == "m1"
        assert result.emails[0].is_read is True
        assert result.total_count == 1
        # The id-walk uses a fixed 500-id page size, not the result page size.
        assert gateway.list_calls[0] == ("hi", None, 500)

    def test_live_empty_results(self) -> None:
        uc = SearchEmailsUseCase(StubGmailGateway(), InMemoryEmailRepository())
        result = uc.execute(SearchEmailsQuery())
        assert result.emails == []
        assert result.total_count == 0

    def test_live_paginates_over_the_id_walk(self) -> None:
        gateway = StubGmailGateway()
        gateway.message_ids = [f"m{i}" for i in range(5)]
        for mid in gateway.message_ids:
            gateway.headers[mid] = _header(mid)
        uc = SearchEmailsUseCase(gateway, InMemoryEmailRepository())
        result = uc.execute(SearchEmailsQuery(query_string="hi", page=2, page_size=2))

        assert result.total_count == 5
        assert [e.message_id for e in result.emails] == ["m2", "m3"]

    def test_live_seen_ids_filtered_before_paging(self) -> None:
        gateway = StubGmailGateway()
        gateway.message_ids = ["m1", "m2", "m3"]
        for mid in gateway.message_ids:
            gateway.headers[mid] = _header(mid)
        uc = SearchEmailsUseCase(gateway, InMemoryEmailRepository())
        result = uc.execute(
            SearchEmailsQuery(query_string="hi", seen_ids=frozenset({"m1"}))
        )
        assert result.total_count == 2
        assert [e.message_id for e in result.emails] == ["m2", "m3"]

    def test_live_include_body_flag_forwarded(self) -> None:
        gateway = StubGmailGateway()
        gateway.message_ids = ["m1"]
        gateway.headers["m1"] = _header("m1", body="B")
        uc = SearchEmailsUseCase(gateway, InMemoryEmailRepository())
        uc.execute(SearchEmailsQuery(query_string="hi", include_body=True))
        assert gateway.metadata_calls[0][1] is True

    def test_live_body_max_length_truncates(self) -> None:
        gateway = StubGmailGateway()
        gateway.message_ids = ["m1"]
        gateway.headers["m1"] = _header("m1", body="0123456789")
        uc = SearchEmailsUseCase(gateway, InMemoryEmailRepository())
        result = uc.execute(SearchEmailsQuery(query_string="hi", body_max_length=4))
        assert result.emails[0].body == "0123"

    def test_cache_mode_uses_repository_with_pagination(self) -> None:
        repo = InMemoryEmailRepository()
        repo.search_results = [_make_email(f"m{i}") for i in range(5)]
        uc = SearchEmailsUseCase(StubGmailGateway(), repo, use_cache=True)
        result = uc.execute(SearchEmailsQuery(query_string="x", page=2, page_size=2))

        assert result.total_count == 5
        assert len(result.emails) == 2
        assert all(isinstance(e, EmailDTO) for e in result.emails)


class TestGetEmailUseCase:
    def test_resolve_by_uuid_from_cache(self) -> None:
        repo = InMemoryEmailRepository()
        email = _make_email()
        repo.add(email)
        uc = GetEmailUseCase(StubGmailGateway(), repo)
        dto = uc.execute(GetEmailQuery(email_id=email.id))
        assert dto.message_id == "msg_1"
        assert dto.body == "Body text"

    def test_uuid_not_found_raises(self) -> None:
        uc = GetEmailUseCase(StubGmailGateway(), InMemoryEmailRepository())
        with pytest.raises(NotFoundError):
            uc.execute(GetEmailQuery(email_id=UUIDId.generate()))

    def test_gmail_id_cache_miss_falls_back_to_gateway(self) -> None:
        gateway = StubGmailGateway()
        gateway.messages["m9"] = GmailMessage(
            id="m9",
            thread_id="t9",
            snippet="s",
            subject="Sub",
            from_="a@b.com",
            to="x@y.com, z@y.com",
            date="2026-01-01",
            labels=["INBOX"],
            body="full body",
            attachments=[],
        )
        uc = GetEmailUseCase(gateway, InMemoryEmailRepository())
        dto = uc.execute(GetEmailQuery(email_id=GmailMessageId("m9")))
        assert dto.body == "full body"
        assert dto.to_addresses == ["x@y.com", "z@y.com"]
        assert dto.is_read is True

    def test_gmail_id_hits_cache_first(self) -> None:
        repo = InMemoryEmailRepository()
        email = _make_email("cached_1")
        repo.add(email)
        uc = GetEmailUseCase(StubGmailGateway(), repo)
        dto = uc.execute(GetEmailQuery(email_id=GmailMessageId("cached_1")))
        assert dto.message_id == "cached_1"

    def test_gmail_id_not_found_anywhere_raises(self) -> None:
        uc = GetEmailUseCase(StubGmailGateway(), InMemoryEmailRepository())
        with pytest.raises(NotFoundError):
            uc.execute(GetEmailQuery(email_id=GmailMessageId("missing")))


class TestGetThreadUseCase:
    def test_resolve_thread_with_full_message_bodies(self) -> None:
        gateway = StubGmailGateway()
        gateway.threads["t1"] = GmailThread(
            id="t1",
            snippet="snip",
            history_id="h1",
            messages=[
                GmailMessage(
                    id="m1",
                    thread_id="t1",
                    snippet="s1",
                    subject="Subj",
                    from_="a@b.com",
                    to="me@example.com",
                    date="2026-01-01",
                    labels=["INBOX"],
                    body="First message body",
                    attachments=[],
                ),
                GmailMessage(
                    id="m2",
                    thread_id="t1",
                    snippet="s2",
                    subject="Re: Subj",
                    from_="me@example.com",
                    to="a@b.com",
                    date="2026-01-02",
                    labels=["INBOX"],
                    body="Reply body",
                    attachments=[],
                ),
            ],
        )
        uc = GetThreadUseCase(gateway)
        dto = uc.execute(GetThreadQuery(thread_id="t1"))

        assert isinstance(dto, ThreadDTO)
        assert dto.subject == "Subj"
        assert len(dto.emails) == 2
        assert dto.emails[0].body == "First message body"
        assert dto.emails[1].body == "Reply body"
        assert dto.email_ids == ["m1", "m2"]
        assert set(dto.participants) == {"a@b.com", "me@example.com"}

    def test_thread_not_found(self) -> None:
        uc = GetThreadUseCase(StubGmailGateway())
        with pytest.raises(NotFoundError):
            uc.execute(GetThreadQuery(thread_id="missing"))


class TestListUnreadUseCase:
    def test_without_label(self) -> None:
        repo = InMemoryEmailRepository()
        repo.add(_make_email("m1"))
        repo.add(_make_email("m2", read=True))
        uc = ListUnreadUseCase(repo)
        result = uc.execute(ListUnreadQuery(limit=10))
        assert len(result) == 1
        assert result[0].message_id == "m1"

    def test_with_label_filter(self) -> None:
        repo = InMemoryEmailRepository()
        repo.add(_make_email("m1", labels=["Work"]))
        repo.add(_make_email("m2", labels=["Personal"]))
        uc = ListUnreadUseCase(repo)
        result = uc.execute(ListUnreadQuery(limit=10, label="Work"))
        assert len(result) == 1
        assert "Work" in result[0].labels


class TestListLabelsUseCase:
    def _gateway(self) -> StubGmailGateway:
        gateway = StubGmailGateway()
        gateway.labels = [
            GmailLabel(id="INBOX", name="INBOX", type="system", color=None),
            GmailLabel(id="Label_1", name="Work", type="user", color="#fff"),
        ]
        return gateway

    def test_all(self) -> None:
        uc = ListLabelsUseCase(self._gateway())
        result = uc.execute(ListLabelsQuery(label_type="all"))
        assert len(result) == 2
        assert all(isinstance(label, LabelDTO) for label in result)

    def test_user_only(self) -> None:
        uc = ListLabelsUseCase(self._gateway())
        result = uc.execute(ListLabelsQuery(label_type="user"))
        assert len(result) == 1
        assert result[0].name == "Work"
        assert result[0].is_system is False

    def test_system_only_marks_is_system(self) -> None:
        uc = ListLabelsUseCase(self._gateway())
        result = uc.execute(ListLabelsQuery(label_type="system"))
        assert result[0].name == "INBOX"
        assert result[0].is_system is True


class TestDTOMapping:
    def test_email_dto_from_entity(self) -> None:
        email = _make_email("m1", labels=["A", "B"])
        email.date_sent = datetime(2026, 1, 1, tzinfo=UTC)
        dto = EmailDTO.from_entity(email)
        assert dto.message_id == "m1"
        assert dto.from_address == "sender@example.com"
        assert dto.to_addresses == ["r@example.com"]
        assert dto.labels == ["A", "B"]
        assert dto.date_sent == datetime(2026, 1, 1, tzinfo=UTC)

    def test_email_dto_handles_missing_from(self) -> None:
        email = Email.from_gmail_message(message_id="m1", thread_id="t1")
        dto = EmailDTO.from_entity(email)
        assert dto.from_address is None
        assert dto.to_addresses == []

    def test_label_dto_from_entity(self) -> None:
        from agentic_mail_mcp.Gmail.Domain.Entities.label import Label

        label = Label(
            id=UUIDId.generate(), label_id="INBOX", name="INBOX", type="system"
        )
        dto = LabelDTO.from_entity(label)
        assert dto.label_id == "INBOX"
        assert dto.is_system is True
