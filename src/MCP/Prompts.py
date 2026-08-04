"""Pre-built MCP prompts guiding agents to use the server effectively.

Each ``PromptDefinition`` wraps a ``PromptTemplate`` (the Intelligence VO, which
validates that every ``{placeholder}`` is supplied at render time) plus the list
of argument names an agent must provide.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.Intelligence.Domain.ValueObjects.prompt_template import PromptTemplate

_SEARCH_STRATEGY = PromptTemplate(
    name="search_strategy",
    template=(
        "Goal: find emails about {goal}.\n"
        "Strategy:\n"
        "1. Start broad with semantic_search using a natural-language description.\n"
        "2. Narrow with search_emails filters: from, subject, date range, label.\n"
        "3. Use unread_only to triage new mail first.\n"
        "4. Open promising results with get_email (or get_thread for conversations)."
    ),
)

_EMAIL_MANAGEMENT = PromptTemplate(
    name="email_management",
    template=(
        "Inbox management workflow:\n"
        "1. list_unread to see what needs attention.\n"
        "2. classify_email to prioritize (urgent/normal/spam/promo).\n"
        "3. summarize_email or extract_action_items for long threads.\n"
        "4. Draft replies with create_draft, then send_draft after human review.\n"
        "5. archive_email once a message is handled; forward_email when delegating."
    ),
)


@dataclass(frozen=True)
class PromptDefinition:
    name: str
    description: str
    template: PromptTemplate
    arguments: list[str] = field(default_factory=list)

    def render(self, **kwargs: str) -> str:
        return self.template.render(**kwargs)


def build_prompts() -> list[PromptDefinition]:
    return [
        PromptDefinition(
            name="search_strategy",
            description="How to search the mailbox effectively for a goal.",
            template=_SEARCH_STRATEGY,
            arguments=["goal"],
        ),
        PromptDefinition(
            name="email_management",
            description="A workflow for triaging and managing the inbox.",
            template=_EMAIL_MANAGEMENT,
            arguments=[],
        ),
    ]
