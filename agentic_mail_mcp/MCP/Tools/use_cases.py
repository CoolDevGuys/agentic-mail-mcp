"""Bundle of application use cases the MCP layer wires into tools.

The MCP layer depends on already-constructed use cases rather than resolving
each dependency itself. A composition root (the DI container) builds this
bundle; tests build it from in-memory fakes. This keeps every tool, the
registry, and the server unit-testable without a live protocol or a fully wired
container.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentic_mail_mcp.Gmail.Application.UseCases.add_label import AddLabelUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.archive_email import (
    ArchiveEmailUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.delete_email import DeleteEmailUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.drafts import (
    CreateDraftUseCase,
    SendDraftUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.forward_email import (
    ForwardEmailUseCase,
)
from agentic_mail_mcp.Gmail.Application.UseCases.get_email import GetEmailUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.get_thread import GetThreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_labels import ListLabelsUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.list_unread import ListUnreadUseCase
from agentic_mail_mcp.Gmail.Application.UseCases.search_emails import (
    SearchEmailsUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.classify_email import (
    ClassifyEmailUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.digest import (
    DailyDigestUseCase,
    WeeklyDigestUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.extract_action_items import (
    ExtractActionItemsUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.suggest_reply import (
    SuggestReplyUseCase,
)
from agentic_mail_mcp.Intelligence.Application.UseCases.summarize_email import (
    SummarizeEmailUseCase,
)
from agentic_mail_mcp.Search.Application.UseCases.semantic_search import (
    SemanticSearchUseCase,
)


@dataclass
class McpUseCases:
    # read
    search_emails: SearchEmailsUseCase
    get_email: GetEmailUseCase
    get_thread: GetThreadUseCase
    list_unread: ListUnreadUseCase
    list_labels: ListLabelsUseCase
    # write (railguarded)
    forward_email: ForwardEmailUseCase
    archive_email: ArchiveEmailUseCase
    delete_email: DeleteEmailUseCase
    create_draft: CreateDraftUseCase
    send_draft: SendDraftUseCase
    add_label: AddLabelUseCase
    # intelligence — optional. Per-email tools register only when internal LLM
    # tools are enabled; digests register when an LLM is configured. Caller-first
    # by default (see MCP prompts), so these are None unless wired.
    summarize_email: SummarizeEmailUseCase | None = None
    classify_email: ClassifyEmailUseCase | None = None
    suggest_reply: SuggestReplyUseCase | None = None
    extract_action_items: ExtractActionItemsUseCase | None = None
    daily_digest: DailyDigestUseCase | None = None
    weekly_digest: WeeklyDigestUseCase | None = None
    # search (optional: requires the `search` extra + a vector backend)
    semantic_search: SemanticSearchUseCase | None = None
