from __future__ import annotations

import pytest

from src.Common.Domain.Exceptions import DomainError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Entities.label import Label


class TestLabelCreation:
    def test_valid_user_label(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="label_1",
            name="Work",
            color="#ff0000",
        )

        assert label.name == "Work"
        assert label.color == "#ff0000"
        assert label.type == "user"
        assert label.is_system is False

    def test_valid_system_label(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="INBOX",
            name="INBOX",
            type="system",
        )

        assert label.name == "INBOX"
        assert label.type == "system"
        assert label.is_system is True

    def test_is_system_based_on_name_not_type(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="INBOX",
            name="INBOX",
            type="user",
        )

        assert label.is_system is True

    def test_default_type_is_user(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="label_2",
            name="Personal",
        )

        assert label.type == "user"
        assert label.is_system is False


class TestLabelRename:
    def test_rename_user_label(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="label_1",
            name="Old Name",
        )

        label.rename("New Name")

        assert label.name == "New Name"

    def test_rename_system_label_blocked(self) -> None:
        label = Label(
            id=UUIDId.generate(),
            label_id="INBOX",
            name="INBOX",
            type="system",
        )

        with pytest.raises(DomainError, match="Cannot rename system label"):
            label.rename("New Name")

        assert label.name == "INBOX"
