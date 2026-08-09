"""A minimal fake of the googleapiclient Gmail resource for adapter tests.

Supports the chained builder pattern (``service.users().messages().get(...)``)
and per-operation outcome queues so a call can raise transient errors before
succeeding.
"""

from __future__ import annotations

from collections import deque
from typing import Any


class FakeHttpError(Exception):
    def __init__(self, status: int) -> None:
        super().__init__(f"HTTP {status}")
        self.resp = type("Resp", (), {"status": status})()


class _Request:
    def __init__(self, service: FakeGmailService, key: str) -> None:
        self._service = service
        self._key = key

    def execute(self) -> Any:
        self._service.executed.append(self._key)
        outcomes = self._service.outcomes.get(self._key)
        outcome = (
            outcomes.popleft() if outcomes else self._service.results.get(self._key, {})
        )
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


class _Attachments:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def get(self, **kwargs: Any) -> _Request:
        self._service.calls.append(("messages.attachments.get", kwargs))
        return _Request(self._service, "messages.attachments.get")


class _Messages:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def _call(self, op: str, **kwargs: Any) -> _Request:
        self._service.calls.append((op, kwargs))
        return _Request(self._service, op)

    def list(self, **kwargs: Any) -> _Request:
        return self._call("messages.list", **kwargs)

    def get(self, **kwargs: Any) -> _Request:
        return self._call("messages.get", **kwargs)

    def send(self, **kwargs: Any) -> _Request:
        return self._call("messages.send", **kwargs)

    def modify(self, **kwargs: Any) -> _Request:
        return self._call("messages.modify", **kwargs)

    def trash(self, **kwargs: Any) -> _Request:
        return self._call("messages.trash", **kwargs)

    def untrash(self, **kwargs: Any) -> _Request:
        return self._call("messages.untrash", **kwargs)

    def delete(self, **kwargs: Any) -> _Request:
        return self._call("messages.delete", **kwargs)

    def batchGet(self, **kwargs: Any) -> _Request:
        return self._call("messages.batchGet", **kwargs)

    def attachments(self) -> _Attachments:
        return _Attachments(self._service)


class _Drafts:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def _call(self, op: str, **kwargs: Any) -> _Request:
        self._service.calls.append((op, kwargs))
        return _Request(self._service, op)

    def create(self, **kwargs: Any) -> _Request:
        return self._call("drafts.create", **kwargs)

    def send(self, **kwargs: Any) -> _Request:
        return self._call("drafts.send", **kwargs)

    def delete(self, **kwargs: Any) -> _Request:
        return self._call("drafts.delete", **kwargs)


class _Labels:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def list(self, **kwargs: Any) -> _Request:
        self._service.calls.append(("labels.list", kwargs))
        return _Request(self._service, "labels.list")


class _History:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def list(self, **kwargs: Any) -> _Request:
        self._service.calls.append(("history.list", kwargs))
        return _Request(self._service, "history.list")


class _Users:
    def __init__(self, service: FakeGmailService) -> None:
        self._service = service

    def messages(self) -> _Messages:
        return _Messages(self._service)

    def drafts(self) -> _Drafts:
        return _Drafts(self._service)

    def labels(self) -> _Labels:
        return _Labels(self._service)

    def history(self) -> _History:
        return _History(self._service)

    def watch(self, **kwargs: Any) -> _Request:
        self._service.calls.append(("watch", kwargs))
        return _Request(self._service, "watch")

    def stop(self, **kwargs: Any) -> _Request:
        self._service.calls.append(("stop", kwargs))
        return _Request(self._service, "stop")


class FakeGmailService:
    def __init__(self) -> None:
        self.results: dict[str, Any] = {}
        self.outcomes: dict[str, deque] = {}
        self.calls: list[tuple[str, dict]] = []
        self.executed: list[str] = []

    def set_result(self, key: str, value: Any) -> None:
        self.results[key] = value

    def set_outcomes(self, key: str, outcomes: list[Any]) -> None:
        self.outcomes[key] = deque(outcomes)

    def users(self) -> _Users:
        return _Users(self)
