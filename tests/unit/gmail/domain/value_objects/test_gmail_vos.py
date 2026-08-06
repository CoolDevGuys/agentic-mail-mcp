import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Gmail.Domain.ValueObjects.gmail_message_id import GmailMessageId
from agentic_mail_mcp.Gmail.Domain.ValueObjects.history_id import HistoryId
from agentic_mail_mcp.Gmail.Domain.ValueObjects.thread_id import ThreadId


class TestGmailMessageId:
    def test_creation(self) -> None:
        mid = GmailMessageId(value="msg_123")
        assert mid.value == "msg_123"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            GmailMessageId(value="")

    def test_equality_same_value(self) -> None:
        m1 = GmailMessageId(value="abc")
        m2 = GmailMessageId(value="abc")
        assert m1 == m2

    def test_inequality_different_value(self) -> None:
        m1 = GmailMessageId(value="abc")
        m2 = GmailMessageId(value="def")
        assert m1 != m2

    def test_hash_consistency(self) -> None:
        m1 = GmailMessageId(value="abc")
        m2 = GmailMessageId(value="abc")
        assert hash(m1) == hash(m2)

    def test_repr(self) -> None:
        mid = GmailMessageId(value="msg_42")
        r = repr(mid)
        assert "GmailMessageId" in r
        assert "msg_42" in r

    def test_usable_in_set(self) -> None:
        s = {
            GmailMessageId(value="a"),
            GmailMessageId(value="a"),
        }
        assert len(s) == 1

    def test_not_equal_to_string(self) -> None:
        mid = GmailMessageId(value="abc")
        assert mid != "abc"


class TestThreadId:
    def test_creation(self) -> None:
        tid = ThreadId(value="thread_456")
        assert tid.value == "thread_456"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            ThreadId(value="")

    def test_equality_same_value(self) -> None:
        t1 = ThreadId(value="thread_1")
        t2 = ThreadId(value="thread_1")
        assert t1 == t2

    def test_inequality_different_value(self) -> None:
        t1 = ThreadId(value="thread_1")
        t2 = ThreadId(value="thread_2")
        assert t1 != t2

    def test_hash_consistency(self) -> None:
        t1 = ThreadId(value="t1")
        t2 = ThreadId(value="t1")
        assert hash(t1) == hash(t2)

    def test_not_equal_to_string(self) -> None:
        tid = ThreadId(value="abc")
        assert tid != "abc"

    def test_not_equal_to_other_vo(self) -> None:
        tid = ThreadId(value="abc")
        mid = GmailMessageId(value="abc")
        assert tid != mid


class TestHistoryId:
    def test_creation(self) -> None:
        hid = HistoryId(value="100")
        assert hid.value == "100"

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            HistoryId(value="")

    def test_equality_same_value(self) -> None:
        h1 = HistoryId(value="42")
        h2 = HistoryId(value="42")
        assert h1 == h2

    def test_inequality_different_value(self) -> None:
        h1 = HistoryId(value="42")
        h2 = HistoryId(value="43")
        assert h1 != h2

    def test_hash_consistency(self) -> None:
        h1 = HistoryId(value="1")
        h2 = HistoryId(value="1")
        assert hash(h1) == hash(h2)

    def test_not_equal_to_string(self) -> None:
        hid = HistoryId(value="42")
        assert hid != "42"

    def test_not_equal_to_other_vo(self) -> None:
        hid = HistoryId(value="abc")
        tid = ThreadId(value="abc")
        assert hid != tid
