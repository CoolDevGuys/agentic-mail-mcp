from __future__ import annotations

from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.thread import Thread
from src.Gmail.Domain.ValueObjects import ThreadId


class ThreadMapper:
    @staticmethod
    def to_domain(gateway_data: dict) -> Thread:
        thread_id = gateway_data.get("thread_id", "")
        email_ids = [UUIDId.from_string(eid) for eid in gateway_data.get("email_ids", [])]

        return Thread.create(
            thread_id=ThreadId(thread_id),
            email_ids=email_ids,
            subject=gateway_data.get("subject", ""),
            snippet=gateway_data.get("snippet", ""),
            participants=gateway_data.get("participants", []),
        )
