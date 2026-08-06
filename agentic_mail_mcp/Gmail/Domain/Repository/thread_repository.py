from __future__ import annotations

from typing import Protocol, runtime_checkable

from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Gmail.Domain.Entities.thread import Thread


@runtime_checkable
class ThreadRepository(Protocol):
    def find_by_id(self, id: UUIDId) -> Thread | None: ...

    def find_by_gmail_thread_id(self, thread_id: str) -> Thread | None: ...

    def save(self, thread: Thread) -> None: ...

    def delete(self, id: UUIDId) -> None: ...
