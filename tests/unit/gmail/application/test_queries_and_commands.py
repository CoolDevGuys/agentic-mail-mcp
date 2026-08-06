from __future__ import annotations

from datetime import date

import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Application.Commands.commands import (
    AddLabelCommand,
    ArchiveEmailCommand,
    CreateDraftCommand,
    DeleteEmailCommand,
    ForwardEmailCommand,
    MarkReadCommand,
    SendDraftCommand,
)
from src.Gmail.Application.Queries.queries import (
    GetEmailQuery,
    GetThreadQuery,
    ListLabelsQuery,
    ListUnreadQuery,
    SearchEmailsQuery,
)
from src.Gmail.Domain.ValueObjects import GmailMessageId, ThreadId


class TestQueries:
    def test_search_emails_query_stores_criteria(self) -> None:
        q = SearchEmailsQuery(
            query_string="invoice",
            from_address="a@b.com",
            subject="hi",
            date_from=date(2026, 1, 1),
            date_to=date(2026, 2, 1),
            has_attachment=True,
            label="Work",
            unread_only=True,
            page=2,
            page_size=10,
        )
        assert q.from_address == "a@b.com"
        assert q.has_attachment is True
        assert q.page == 2

    @pytest.mark.parametrize("page,page_size", [(0, 10), (1, 0), (-1, 10)])
    def test_search_emails_query_rejects_bad_pagination(
        self, page: int, page_size: int
    ) -> None:
        with pytest.raises(ValidationError):
            SearchEmailsQuery(page=page, page_size=page_size)

    def test_get_email_query_accepts_uuid(self) -> None:
        uid = UUIDId.generate()
        q = GetEmailQuery(email_id=uid)
        assert q.is_uuid is True

    def test_get_email_query_accepts_gmail_message_id(self) -> None:
        q = GetEmailQuery(email_id=GmailMessageId("msg_1"))
        assert q.is_uuid is False

    def test_get_email_query_rejects_other_types(self) -> None:
        with pytest.raises(ValidationError):
            GetEmailQuery(email_id="raw-string")  # type: ignore[arg-type]

    def test_get_thread_query_from_string_and_vo(self) -> None:
        assert GetThreadQuery(thread_id="t1").value == "t1"
        assert GetThreadQuery(thread_id=ThreadId("t2")).value == "t2"

    def test_get_thread_query_rejects_empty(self) -> None:
        with pytest.raises(ValidationError):
            GetThreadQuery(thread_id="")

    def test_list_unread_query_rejects_bad_limit(self) -> None:
        with pytest.raises(ValidationError):
            ListUnreadQuery(limit=0)

    def test_list_labels_query_default_all(self) -> None:
        assert ListLabelsQuery().label_type == "all"

    def test_list_labels_query_rejects_bad_type(self) -> None:
        with pytest.raises(ValidationError):
            ListLabelsQuery(label_type="bogus")


class TestCommands:
    def test_forward_requires_recipient(self) -> None:
        with pytest.raises(ValidationError):
            ForwardEmailCommand(message_id="m1", to_address="")

    def test_forward_requires_message_id(self) -> None:
        with pytest.raises(ValidationError):
            ForwardEmailCommand(message_id="", to_address="x@y.com")

    def test_forward_valid(self) -> None:
        cmd = ForwardEmailCommand(message_id="m1", to_address="x@y.com")
        assert cmd.include_original is True

    def test_archive_requires_target(self) -> None:
        with pytest.raises(ValidationError):
            ArchiveEmailCommand()

    def test_archive_with_thread_id(self) -> None:
        assert ArchiveEmailCommand(thread_id="t1").thread_id == "t1"

    def test_delete_defaults_non_permanent(self) -> None:
        assert DeleteEmailCommand(message_id="m1").permanent is False

    def test_create_draft_requires_recipient(self) -> None:
        with pytest.raises(ValidationError):
            CreateDraftCommand(to_address="")

    def test_create_draft_valid(self) -> None:
        cmd = CreateDraftCommand(to_address="x@y.com", subject="s")
        assert cmd.attachments == []

    def test_send_draft_requires_id(self) -> None:
        with pytest.raises(ValidationError):
            SendDraftCommand(draft_id="")

    def test_add_label_requires_name(self) -> None:
        with pytest.raises(ValidationError):
            AddLabelCommand(message_id="m1", label_name="")

    def test_add_label_valid(self) -> None:
        cmd = AddLabelCommand(message_id="m1", label_name="Work")
        assert cmd.label_name == "Work"

    def test_mark_read_valid(self) -> None:
        assert MarkReadCommand(message_id="m1").message_id == "m1"

    def test_mark_read_requires_message_id(self) -> None:
        with pytest.raises(ValidationError):
            MarkReadCommand(message_id="")

    def test_add_label_requires_message_id(self) -> None:
        with pytest.raises(ValidationError):
            AddLabelCommand(message_id="", label_name="Work")
