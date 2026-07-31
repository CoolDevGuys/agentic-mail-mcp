import json
import logging
import re
import uuid
from datetime import UTC, datetime
from logging import Filter
from typing import Any, ClassVar


class RedactionFilter(Filter):
    _SENSITIVE_PATTERNS: ClassVar[list[re.Pattern[str]]] = [
        re.compile(r"(Bearer\s+)(\S+)", re.IGNORECASE),
        re.compile(r"(token['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE),
        re.compile(r"(password['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE),
        re.compile(r"(secret['\"]?\s*[:=]\s*['\"]?)(\S+)", re.IGNORECASE),
        re.compile(r"(eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+)"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = self._redact(str(record.msg))
        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: self._redact(str(v)) for k, v in record.args.items()
                }
            elif isinstance(record.args, tuple):
                record.args = tuple(
                    self._redact(str(a)) for a in record.args
                )
        return True

    def _redact(self, text: str) -> str:
        for pattern in self._SENSITIVE_PATTERNS:
            text = pattern.sub(r"\1[REDACTED]", text)
        return text


class JsonFormatter(logging.Formatter):
    def __init__(self) -> None:
        super().__init__()
        self._correlation_id = None

    def format(self, record: logging.LogRecord) -> str:
        if not hasattr(record, "correlation_id"):  # type: ignore[attr-defined]
            record.correlation_id = getattr(  # type: ignore[attr-defined]
                self, "_correlation_id", None
            ) or str(uuid.uuid4())

        log_entry: dict[str, Any] = {
            "correlation_id": record.correlation_id,  # type: ignore[attr-defined]
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "module": record.module,
            "message": record.getMessage(),
        }

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


def setup_logging(
    level: str = "INFO",
    json_format: bool = True,
) -> logging.Logger:
    logger = logging.getLogger("gmail_mcp")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    handler = logging.StreamHandler()
    handler.setFormatter(
        JsonFormatter() if json_format else logging.Formatter("%(message)s")
    )
    handler.addFilter(RedactionFilter())

    logger.addHandler(handler)
    return logger
