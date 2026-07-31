import json
import logging

import pytest

from src.Bootstrap.Logging import JsonFormatter, RedactionFilter, setup_logging


class TestRedactionFilter:
    def test_redacts_bearer_tokens(self):
        filter_ = RedactionFilter()
        text = "Auth: Bearer abc123secret"
        result = filter_._redact(text)
        assert "abc123secret" not in result
        assert "[REDACTED]" in result

    def test_redacts_passwords(self):
        filter_ = RedactionFilter()
        text = 'password: mysecretpass'
        result = filter_._redact(text)
        assert "mysecretpass" not in result
        assert "[REDACTED]" in result

    def test_redacts_secrets(self):
        filter_ = RedactionFilter()
        text = 'secret="topsecret"'
        result = filter_._redact(text)
        assert "topsecret" not in result
        assert "[REDACTED]" in result

    def test_redacts_jwts(self):
        filter_ = RedactionFilter()
        text = "token: eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJ1c2VyIn0.abc123def456"
        result = filter_._redact(text)
        assert "eyJhbGciOiJIUzI1NiJ9" not in result
        assert "[REDACTED]" in result

    def test_does_not_modify_safe_text(self):
        filter_ = RedactionFilter()
        text = "This is a normal log message"
        result = filter_._redact(text)
        assert result == text

    def test_filter_returns_true(self):
        filter_ = RedactionFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="test", args=(), exc_info=None
        )
        assert filter_.filter(record) is True

    def test_redacts_msg(self):
        filter_ = RedactionFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="Bearer secret123", args=(), exc_info=None
        )
        filter_.filter(record)
        assert "secret123" not in str(record.msg)

    def test_redacts_tuple_args(self):
        filter_ = RedactionFilter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="", lineno=0, msg="%s", args=("Bearer secret123",), exc_info=None
        )
        filter_.filter(record)
        assert "secret123" not in str(record.args)


class TestJsonFormatter:
    def test_produces_valid_json(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=0, msg="hello", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert isinstance(parsed, dict)

    def test_contains_required_fields(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="test.py", lineno=0, msg="hello", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert "correlation_id" in parsed
        assert "timestamp" in parsed
        assert "level" in parsed
        assert "module" in parsed
        assert "message" in parsed

    def test_correlation_id_is_uuid(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=0, msg="hello", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        correlation_id = parsed["correlation_id"]
        assert len(correlation_id) == 36

    def test_level_name(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="test.py", lineno=0, msg="hello", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["level"] == "ERROR"

    def test_message_content(self):
        formatter = JsonFormatter()
        record = logging.LogRecord(
            name="test", level=logging.INFO, pathname="test.py", lineno=0, msg="test-message", args=(), exc_info=None
        )
        output = formatter.format(record)
        parsed = json.loads(output)
        assert parsed["message"] == "test-message"


@pytest.fixture(autouse=True)
def _clean_logger():
    """Remove handlers from the gmail_mcp logger after each test."""
    yield
    logger = logging.getLogger("gmail_mcp")
    logger.handlers.clear()


class TestSetupLogging:
    def test_returns_logger(self):
        logger = setup_logging()
        assert isinstance(logger, logging.Logger)

    def test_logger_name(self):
        logger = setup_logging()
        assert logger.name == "gmail_mcp"

    def test_sets_log_level(self):
        logger = setup_logging(level="DEBUG")
        assert logger.level == logging.DEBUG

    def test_json_format_true(self):
        logger = setup_logging(json_format=True)
        handler = logger.handlers[0]
        assert isinstance(handler.formatter, JsonFormatter)

    def test_json_format_false(self):
        logger = setup_logging(json_format=False)
        handler = logger.handlers[0]
        assert not isinstance(handler.formatter, JsonFormatter)

    def test_has_redaction_filter(self):
        logger = setup_logging()
        handler = logger.handlers[0]
        filter_types = [type(f).__name__ for f in handler.filters]
        assert "RedactionFilter" in filter_types
