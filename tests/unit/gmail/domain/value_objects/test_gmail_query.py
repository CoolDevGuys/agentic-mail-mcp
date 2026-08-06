from datetime import date

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Gmail.Domain.ValueObjects.gmail_query import GmailQuery


class TestGmailQueryCreation:
    def test_valid_query(self) -> None:
        q = GmailQuery(value="from:alice@example.com")
        assert q.value == "from:alice@example.com"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            GmailQuery(value="")

    def test_rejects_exceeds_500_characters(self) -> None:
        long_query = "a" * 501
        with pytest.raises(ValidationError):
            GmailQuery(value=long_query)

    def test_accepts_500_characters(self) -> None:
        exact_query = "a" * 500
        q = GmailQuery(value=exact_query)
        assert len(q.value) == 500


class TestGmailQueryBuilders:
    def test_from_sender(self) -> None:
        q = GmailQuery.from_sender("alice@example.com")
        assert q.value == "from:alice@example.com"

    def test_with_subject(self) -> None:
        q = GmailQuery.with_subject("Hello")
        assert q.value == "subject:Hello"

    def test_date_range_after(self) -> None:
        q = GmailQuery.date_range(after=date(2024, 1, 1))
        assert q.value == "after:2024-01-01"

    def test_date_range_before(self) -> None:
        q = GmailQuery.date_range(before=date(2024, 12, 31))
        assert q.value == "before:2024-12-31"

    def test_date_range_both(self) -> None:
        q = GmailQuery.date_range(after=date(2024, 1, 1), before=date(2024, 12, 31))
        assert q.value == "after:2024-01-01 before:2024-12-31"

    def test_date_range_neither_raises(self) -> None:
        with pytest.raises(ValidationError):
            GmailQuery.date_range()

    def test_has_attachment(self) -> None:
        q = GmailQuery.has_attachment()
        assert q.value == "has:attachment"

    def test_with_label(self) -> None:
        q = GmailQuery.with_label("important")
        assert q.value == "important"

    def test_unread(self) -> None:
        q = GmailQuery.unread()
        assert q.value == "is:unread"


class TestGmailQueryCombination:
    def test_and_combines_with_space(self) -> None:
        q1 = GmailQuery.from_sender("alice@example.com")
        q2 = GmailQuery.with_subject("Hello")
        combined = q1.and_(q2)
        assert combined.value == "from:alice@example.com subject:Hello"
        assert isinstance(combined, GmailQuery)

    def test_and_is_not_mutating(self) -> None:
        q1 = GmailQuery.from_sender("alice@example.com")
        q2 = GmailQuery.unread()
        _ = q1.and_(q2)
        assert q1.value == "from:alice@example.com"
        assert q2.value == "is:unread"

    def test_and_chaining(self) -> None:
        q1 = GmailQuery.from_sender("alice@example.com")
        q2 = GmailQuery.unread()
        q3 = GmailQuery.has_attachment()
        combined = q1.and_(q2).and_(q3)
        assert combined.value == "from:alice@example.com is:unread has:attachment"

    def test_and_respects_500_char_limit(self) -> None:
        q1 = GmailQuery(value="a" * 400)
        q2 = GmailQuery(value="b" * 400)
        with pytest.raises(ValidationError):
            q1.and_(q2)


class TestGmailQueryEquality:
    def test_same_value_equals(self) -> None:
        q1 = GmailQuery(value="from:alice@example.com")
        q2 = GmailQuery(value="from:alice@example.com")
        assert q1 == q2

    def test_different_values_not_equal(self) -> None:
        q1 = GmailQuery(value="from:alice@example.com")
        q2 = GmailQuery(value="from:bob@example.com")
        assert q1 != q2

    def test_not_equal_to_string(self) -> None:
        q = GmailQuery(value="hello")
        assert q != "hello"

    def test_equal_hashes(self) -> None:
        q1 = GmailQuery(value="test")
        q2 = GmailQuery(value="test")
        assert hash(q1) == hash(q2)

    def test_usable_in_set(self) -> None:
        s = {
            GmailQuery(value="q1"),
            GmailQuery(value="q1"),
        }
        assert len(s) == 1
