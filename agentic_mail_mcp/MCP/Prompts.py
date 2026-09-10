"""Pre-built MCP prompts guiding agents to use the server effectively.

Each ``PromptDefinition`` wraps a ``PromptTemplate`` (the Intelligence VO, which
validates that every ``{placeholder}`` is supplied at render time) plus the list
of argument names an agent must provide.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from agentic_mail_mcp.Intelligence.Domain.ValueObjects.prompt_template import (
    PromptTemplate,
)

_SEARCH_STRATEGY = PromptTemplate(
    name="search_strategy",
    template=(
        "Goal: find emails about {goal}.\n"
        "Strategy:\n"
        "1. Start broad with semantic_search using a natural-language description.\n"
        "2. Narrow with search_emails filters: from, subject, date range, label, "
        "direction (received/sent).\n"
        "3. Keep results small: pass `fields` for only what you need "
        '(e.g. ["subject", "from", "date"]) and cap bodies with '
        "`body_max_length`; fetch full bodies only for the few you open.\n"
        "4. Use unread_only to triage new mail first; pass `seen_ids` to skip "
        "messages you have already processed.\n"
        "5. Open promising results with get_email (or get_thread for conversations)."
    ),
)

_EMAIL_MANAGEMENT = PromptTemplate(
    name="email_management",
    template=(
        "Inbox management workflow:\n"
        "1. list_unread to see what needs attention.\n"
        "2. Use the classify/summarize prompts to prioritize and digest.\n"
        "3. Draft replies with create_draft, then send_draft after human review.\n"
        "4. archive_email once a message is handled; forward_email when delegating."
    ),
)

# Caller-first intelligence: the calling agent is itself an LLM, so per-email
# reasoning is a prompt the agent runs on data it fetches with get_email —
# no extra server-side inference, no latency, no LLM key required.
_SUMMARIZE_EMAIL = PromptTemplate(
    name="summarize_email",
    template=(
        "Fetch the email with id {email_id} using the get_email tool, then write a "
        "concise 2-3 sentence summary of what it says and what (if anything) it asks "
        "of the reader."
    ),
)

_CLASSIFY_EMAIL = PromptTemplate(
    name="classify_email",
    template=(
        "Fetch the email with id {email_id} using the get_email tool, then classify "
        "it: category (one of urgent, normal, spam, promo), priority (1-5, 5 = most "
        "urgent), and a one-line justification."
    ),
)

_DRAFT_REPLY = PromptTemplate(
    name="draft_reply",
    template=(
        "Fetch the email with id {email_id} using the get_email tool, then draft a "
        "reply in the user's voice. Do NOT send it — propose the draft for review, "
        "and offer to save it with create_draft."
    ),
)

_EXTRACT_ACTION_ITEMS = PromptTemplate(
    name="extract_action_items",
    template=(
        "Fetch the email with id {email_id} using the get_email tool, then list any "
        "action items as bullets, each with an owner and a due date if stated "
        "(otherwise 'no due date')."
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
        PromptDefinition(
            name="summarize_email",
            description="Summarize an email (run by the calling agent).",
            template=_SUMMARIZE_EMAIL,
            arguments=["email_id"],
        ),
        PromptDefinition(
            name="classify_email",
            description="Classify an email by category and priority (caller-run).",
            template=_CLASSIFY_EMAIL,
            arguments=["email_id"],
        ),
        PromptDefinition(
            name="draft_reply",
            description="Draft a reply to an email for review (caller-run).",
            template=_DRAFT_REPLY,
            arguments=["email_id"],
        ),
        PromptDefinition(
            name="extract_action_items",
            description="Extract action items from an email (caller-run).",
            template=_EXTRACT_ACTION_ITEMS,
            arguments=["email_id"],
        ),
    ]
