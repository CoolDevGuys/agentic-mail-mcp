"""Composition root: wire the infrastructure adapters into use cases.

This is where concrete implementations meet the application layer. It builds the
``McpUseCases`` bundle and a ``ResourceContext`` from ``Settings`` so the MCP
server can register and serve real tools.

Design notes:
- **Gmail** is wrapped in a ``LazyGmailGateway`` so tools register at startup even
  before the user has authorized; the first call builds the authenticated client
  (or fails with a clear "run `agentic-mail-mcp auth`" message).
- **Persistence** is synchronous SQLAlchemy; the schema is created via the Alembic
  migrations so runtime matches ``migrations/``.
- **Intelligence** always registers (the LLM client is cheap to construct and
  fails gracefully at call time if unconfigured).
- **Search** is optional: it needs the ``search`` extra (sentence-transformers +
  sqlite-vec). When unavailable it is skipped and the ``semantic_search`` tool is
  simply not registered.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.Common.Domain.Events import InMemoryEventBus
from agentic_mail_mcp.Common.Infrastructure.Clock import SystemClock
from agentic_mail_mcp.Common.Infrastructure.IdGenerator import UuidIdGenerator
from agentic_mail_mcp.Common.Infrastructure.Persistence.database import (
    create_database_engine,
    create_session_factory,
)
from agentic_mail_mcp.Common.Infrastructure.Persistence.migrations_runner import (
    apply_migrations,
)
from agentic_mail_mcp.Common.Railguards.config import RailguardConfig
from agentic_mail_mcp.Common.Railguards.validator import RailguardValidator
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
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository
from agentic_mail_mcp.Gmail.Infrastructure.Google.lazy_gateway import LazyGmailGateway
from agentic_mail_mcp.Gmail.Infrastructure.Google.oauth_provider import (
    GmailOAuthProvider,
)
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.cached_email_repository import (
    CachedEmailRepository,
)
from agentic_mail_mcp.Gmail.Infrastructure.Persistence.SqlAlchemy.Repositories.sqlite_email_repository import (
    SqliteEmailRepository,
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
from agentic_mail_mcp.Intelligence.Infrastructure.InMemory.repositories import (
    InMemoryClassificationRepository,
    InMemorySuggestionRepository,
    InMemorySummaryRepository,
)
from agentic_mail_mcp.Intelligence.Infrastructure.LlamaCpp.llama_cpp_gateway import (
    LlamaCppGateway,
)
from agentic_mail_mcp.MCP.Resources import ResourceContext
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases

logger = logging.getLogger(__name__)


_PLACEHOLDER_KEYS = {"", "your-api-key"}


def llm_configured(settings: Settings) -> bool:
    """True when a usable LLM is configured (so digests / internal tools work)."""
    llm = settings.llm
    if llm.provider == "llamacpp":
        return bool(llm.model_path)
    return llm.api_key not in _PLACEHOLDER_KEYS


def resolve_client_config(settings: Settings) -> dict | None:
    """Resolve the user's own Google OAuth client config (bring-your-own app).

    Prefers the downloaded ``credentials.json`` (``client_secrets_file``); falls
    back to an explicit ``client_id`` / ``client_secret``. Returns ``None`` when
    neither is configured, so callers can give clear guidance.
    """
    gmail = settings.gmail
    if gmail.client_secrets_file:
        path = Path(gmail.client_secrets_file).expanduser()
        if path.exists():
            data = json.loads(path.read_text())
            # Google downloads this as {"installed": {...}} (Desktop app) or
            # {"web": {...}}; InstalledAppFlow.from_client_config accepts either.
            if "installed" in data or "web" in data:
                return data
    if gmail.oauth_client_id and gmail.oauth_client_secret:
        return {
            "installed": {
                "client_id": gmail.oauth_client_id,
                "client_secret": gmail.oauth_client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": ["http://localhost"],
            }
        }
    return None


def build_oauth_provider(settings: Settings) -> GmailOAuthProvider:
    """Build the OAuth provider (token persistence + interactive authorization)."""
    gmail = settings.gmail
    return GmailOAuthProvider(
        gmail.token_storage_path,
        gmail.token_encryption_key,
        scopes=list(gmail.scopes),
        client_config=resolve_client_config(settings),
    )


def _build_semantic_search(settings: Settings, email_repo: EmailRepository | None = None):
    """Best-effort search wiring; returns None if the backend is unavailable.

    The email repository (when supplied) lets results carry the Gmail message
    id of matched emails.
    """
    try:
        from agentic_mail_mcp.Search.Application.UseCases.semantic_search import (
            SemanticSearchUseCase,
        )
        from agentic_mail_mcp.Search.Infrastructure.BGE.bge_embedding_gateway import (
            BgeEmbeddingGateway,
        )
        from agentic_mail_mcp.Search.Infrastructure.SqliteVec.sqlite_vec_repository import (
            SqliteVecRepository,
        )

        dimension = settings.search.embedding_dimension
        embedding = BgeEmbeddingGateway(
            model_name=settings.search.embedding_model, dimension=dimension
        )
        vector_repo = SqliteVecRepository.create(
            "./gmail_mcp_vectors.db", dimension=dimension
        )
        return (
            SemanticSearchUseCase(embedding, vector_repo, email_repository=email_repo),
            vector_repo,
        )
    except Exception as exc:  # noqa: BLE001  # pragma: no cover - optional extra
        logger.warning(
            "Semantic search unavailable (install the 'search' extra to enable): %s",
            exc,
        )
        return None, None


def build_use_cases(
    settings: Settings, gateway: GmailGateway | None = None
) -> McpUseCases:
    """Assemble every use case from configuration.

    ``gateway`` can be injected (tests); by default a lazy, OAuth-backed Gmail
    gateway is used.
    """
    # --- shared ---
    event_bus = InMemoryEventBus()
    clock = SystemClock()
    id_gen = UuidIdGenerator()
    validator = RailguardValidator(RailguardConfig.from_settings(settings.railguards))

    # --- gmail gateway (lazy OAuth-backed by default) ---
    if gateway is None:
        gateway = LazyGmailGateway(build_oauth_provider(settings))

    # --- persistence ---
    # Gmail is the source of truth. The email repository is a read-through cache
    # over the gateway: single reads are live (fresh, full body), metadata is
    # cached (never bodies), and lists are served from that cache within a TTL.
    engine = create_database_engine(settings.database.url)
    apply_migrations(settings.database.url)
    session_factory = create_session_factory(engine)
    email_repo: EmailRepository = CachedEmailRepository(
        SqliteEmailRepository(session_factory),
        gateway,
        clock=clock,
        ttl_seconds=settings.database.cache_ttl_seconds,
    )
    # --- search (optional) ---
    semantic_search, _vector_repo = _build_semantic_search(settings, email_repo)

    uses = McpUseCases(
        search_emails=SearchEmailsUseCase(gateway, email_repo),
        get_email=GetEmailUseCase(gateway, email_repo),
        get_thread=GetThreadUseCase(gateway),
        list_unread=ListUnreadUseCase(email_repo),
        list_labels=ListLabelsUseCase(gateway),
        forward_email=ForwardEmailUseCase(gateway, validator, email_repo, event_bus),
        archive_email=ArchiveEmailUseCase(gateway, validator, email_repo, event_bus),
        delete_email=DeleteEmailUseCase(gateway, validator, email_repo, event_bus),
        create_draft=CreateDraftUseCase(gateway, validator),
        send_draft=SendDraftUseCase(gateway, validator),
        add_label=AddLabelUseCase(gateway, validator, email_repo, event_bus),
        semantic_search=semantic_search,
    )

    # --- intelligence (caller-first) ---
    # The calling agent is itself an LLM, so per-email reasoning is exposed as MCP
    # prompts by default. Digests do map-reduce over many emails (real context
    # savings) so they register whenever an LLM is configured. The per-email tools
    # are an opt-in escape hatch (llm.internal_tools=true).
    if llm_configured(settings):
        llm = LlamaCppGateway.from_settings(settings)
        uses.daily_digest = DailyDigestUseCase(email_repo, llm, clock, event_bus)
        uses.weekly_digest = WeeklyDigestUseCase(email_repo, llm, clock, event_bus)
        if settings.llm.internal_tools:
            uses.summarize_email = SummarizeEmailUseCase(
                email_repo, llm, InMemorySummaryRepository(), clock, id_gen
            )
            uses.classify_email = ClassifyEmailUseCase(
                email_repo, llm, InMemoryClassificationRepository(), clock, id_gen
            )
            uses.suggest_reply = SuggestReplyUseCase(
                email_repo, llm, InMemorySuggestionRepository(), clock, id_gen
            )
            uses.extract_action_items = ExtractActionItemsUseCase(email_repo, llm)

    return uses


def build_resource_context(settings: Settings) -> ResourceContext:
    return ResourceContext(
        account_email=settings.gmail.oauth_client_id.split(".")[0] or "connected",
        access_level=settings.railguards.access_level,
    )
