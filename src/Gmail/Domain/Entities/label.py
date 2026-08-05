from __future__ import annotations

from dataclasses import dataclass

from src.Common.Domain.Exceptions import DomainError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId

SYSTEM_LABELS = frozenset(
    {
        "INBOX",
        "SPAM",
        "TRASH",
        "SENT",
        "DRAFT",
        "IMPORTANT",
        "STARRED",
        "UNREAD",
        "CATEGORY_PERSONAL",
        "CATEGORY_PROMOTIONS",
        "CATEGORY_UPDATES",
        "CATEGORY_FORUMS",
    }
)


@dataclass
class Label:
    id: UUIDId
    label_id: str
    name: str
    color: str = ""
    type: str = "user"

    @property
    def is_system(self) -> bool:
        return self.name in SYSTEM_LABELS

    def rename(self, new_name: str) -> None:
        if self.is_system:
            raise DomainError(f"Cannot rename system label: {self.name}")
        self.name = new_name
