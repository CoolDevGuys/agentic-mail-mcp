from __future__ import annotations

import re

import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.MCP.Prompts import build_prompts


def _prompt(name):
    return next(p for p in build_prompts() if p.name == name)


class TestPrompts:
    def test_two_prompts_registered(self) -> None:
        names = {p.name for p in build_prompts()}
        assert names == {"search_strategy", "email_management"}

    def test_search_strategy_renders_with_goal(self) -> None:
        rendered = _prompt("search_strategy").render(goal="unpaid invoices")
        assert "unpaid invoices" in rendered
        assert not re.search(r"\{[a-zA-Z_]+\}", rendered)

    def test_email_management_renders_without_arguments(self) -> None:
        rendered = _prompt("email_management").render()
        assert "list_unread" in rendered
        assert not re.search(r"\{[a-zA-Z_]+\}", rendered)

    def test_missing_argument_raises(self) -> None:
        with pytest.raises(ValidationError):
            _prompt("search_strategy").render()
