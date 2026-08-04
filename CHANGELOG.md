# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### ⚠ Breaking

- **Railguards default is now read-only** (Phase 6): `railguards.access_level` defaults to `read_only` (was `owner`), so all write operations (forward/archive/delete/draft) are denied until a deployment sets `GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL=read_write`.

### Fixed

- **Environment-variable configuration now works** (Phase 8): the `Settings`
  sub-sections (`gmail`, `database`, `railguards`, `mcp`, `llm`, `search`,
  `notifications`, `logging`) previously ignored their `GMAIL_MCP_<SECTION>_<FIELD>`
  environment variables and always used defaults. Each section now carries its
  own env prefix, so documented variables such as
  `GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL`, `GMAIL_MCP_MCP_TRANSPORT`, and
  `GMAIL_MCP_DATABASE_URL` take effect — required for pip/Docker deployments to
  be configurable.

### Added

- **Distribution and polish** (Phase 8)
  - `LICENSE` (MIT); `pyproject.toml` distribution metadata (`readme`,
    `project.urls`, `license-files`) and a scoped sdist target producing a clean
    source distribution + wheel with the `gmail-mcp-server` entry point
  - `specs/docs/api.md` — the MCP tool/resource/prompt reference with input
    schemas, output shapes, and the structured error format
  - Architecture ADRs `0002`–`0005` (DDD + vertical slicing, SQLite/PostgreSQL
    persistence, railguards write-safety, MCP stdio transport)
  - Expanded `README.md` (tool catalog, railguards security model, stdio
    integration example, contributing) and `RELEASING.md` (PyPI + multi-arch
    Docker publish flow)
  - Multi-stage `Dockerfile` (builder + slim non-root runtime, health check),
    multi-arch build support
  - End-to-end MCP session tests (`tests/e2e/`) covering the read/write tool
    flow, railguard enforcement, and a container health-check smoke test
  - Removed the superseded pre-DDD `main.py` / `server.py` skeletons from the
    repo root (replaced by `src/MCP/Server.py` and `src/Bootstrap/cli.py`)

- **MCP server layer** (Phase 7)
  - `create_server` bootstrap that assembles the server from the dependency container and integrates the application lifespan; configurable transport (`stdio` default, streamable HTTP) via `Settings.mcp.transport`; the `gmail-mcp-server` console entry point launches it
  - `ToolRegistry` with category-grouped tools (read/write/intelligence/search) and JSON-Schema input schemas; **defense-in-depth**: write-category tools are not registered when `railguards.access_level` is `read_only`, so they are never exposed to the agent
  - Read tools: `search_emails`, `get_email`, `get_thread`, `list_unread`, `list_labels`
  - Write tools (railguarded): `forward_email`, `archive_email`, `delete_email`, `create_draft`, `send_draft`, `add_label`
  - Intelligence tools: `summarize_email`, `classify_email`, `suggest_reply`, `extract_action_items`, `daily_digest`, `weekly_digest`
  - Search tool: `semantic_search`
  - MCP resources (account info, watch status, index status) and prompts (search strategy, email management); structured tool-error mapping for railguard denials, missing entities, and invalid input
  - `AddLabelUseCase` (railguarded) emitting `EmailLabeled`; digest use cases accept an optional date anchor
  - `Settings.mcp.transport` (`stdio` default)
- **Railguards framework** (Phase 6)
  - `RailguardConfig` (access level, recipient allowlist with address/domain matching, action blocklist, windowed rate limits, archive-first policy) and `RailguardValidator` raising `PermissionError` on violation
  - `audit_log` table, `AuditLogRepository` (SQLite), and `AuditLogHandler` event subscriber recording every write with a correlation id
  - Railguarded write use cases: `ForwardEmailUseCase`, `ArchiveEmailUseCase`, `DeleteEmailUseCase` (soft-delete default, archive-first for permanent), `CreateDraftUseCase` / `SendDraftUseCase` (draft-first sending)
  - `GmailGateway` draft operations (`create_draft`/`send_draft`/`delete_draft`) and their `GmailApiGateway` implementation
  - `Settings.railguards.archive_first_policy`; Alembic migration `0002`
- **Shared domain primitives** (Phase 2)
  - `ValueObject` base class with structural equality, hashing, and repr
  - `UUIDId` value object wrapping `uuid.UUID` with `generate()` factory
  - Typed exception hierarchy: `DomainError`, `ValidationError`, `NotFoundError`, `PermissionError`, `ConcurrencyError`
  - `EventBus` protocol and `InMemoryEventBus` implementation
  - `Specification[T]` pattern with `And`, `Or`, `Not` composables
  - `Clock` protocol with `SystemClock` and `FrozenClock` implementations
  - `IdGenerator` protocol with `UuidIdGenerator` implementation
- Exhaustive unit test coverage for all shared primitives
- **Domain models for all bounded contexts** (Phase 3)
  - Gmail: `Email`, `Thread`, `Attachment`, `Label` aggregates; `EmailAddress`, `GmailMessageId`, `ThreadId`, `HistoryId`, `GmailQuery` value objects; repository and `GmailGateway` ports; mappers; domain events
  - Intelligence: `Summary`, `Classification`, `Suggestion` entities; `PromptTemplate`, `ModelConfig` value objects; `LlmGateway` port
  - Search: `SearchDocument` entity; `EmbeddingGateway` and `VectorSearchRepository` ports
  - Notification: `ImportantEmailDetected`, `InboxChanged`, `DigestReady` events; `NotificationGateway` port
- **Application use cases** (Phase 4)
  - Gmail read use cases: `SearchEmailsUseCase`, `GetEmailUseCase`, `GetThreadUseCase`, `ListUnreadUseCase`, `ListLabelsUseCase`; query/command objects and read DTOs
  - Intelligence use cases: `SummarizeEmailUseCase`, `SuggestReplyUseCase`, `ClassifyEmailUseCase`, `DailyDigestUseCase`, `WeeklyDigestUseCase`, `ExtractActionItemsUseCase`
  - Search use cases: `SemanticSearchUseCase`, `IndexEmailUseCase`, `RebuildIndexUseCase`
  - Notification use cases: `NotifyImportantEmailUseCase`, `PublishInboxEventUseCase` (domain-event subscribers)

### Changed

- `EventBus` is now generic over concrete event types: handlers are registered and dispatched by the event's exact type, so domain events are no longer required to inherit `DomainEvent` (it remains an optional base for standard metadata).
- **Database default is now a synchronous SQLite driver** (`sqlite:///…`) to match the synchronous repository ports (Phase 5). Set `GMAIL_MCP_DATABASE_URL` to a `postgresql+psycopg2://…` URL for PostgreSQL.

### Added (Phase 5 — Infrastructure Adapters)

- **Persistence**: synchronous SQLAlchemy engine/session wiring with a UTC-normalizing datetime type; ORM models and domain↔ORM mappers for Email/Thread/Attachment/Label; `SqliteEmailRepository` / `SqliteThreadRepository`; initial Alembic migration (`alembic.ini` + `migrations/`); PostgreSQL repository variants sharing the schema.
- **Gmail Google adapter**: `GmailOAuthProvider` (Fernet-encrypted token storage), `GmailApiGateway` (Gmail API with retry/backoff and rate limiting), `GmailWatcher` (push notifications + webhook parsing), `GmailHistorySynchronizer` (idempotent history sync emitting domain events).
- **Intelligence**: `LlamaCppGateway` implementing `LlmGateway` over an OpenAI-compatible endpoint or a local llama.cpp model.
- **Search**: `BgeEmbeddingGateway` (`EmbeddingGateway`); `SqliteVecRepository` (default) and `PgVectorRepository` (optional) implementing `VectorSearchRepository`, verified interchangeable by a shared contract test.
- **Notification**: `WebhookNotificationGateway` and `RedisNotificationGateway` implementing `NotificationGateway`.
- **Wiring**: `register_infrastructure()` binds the default adapter stack on the DI container.
- New Settings keys (`llm.base_url`, `llm.model_path`, `search.*`) and optional dependency extras (`postgresql`, `search`, `notifications`, `llm`); see `specs/docs/configuration.md` and `specs/docs/data-model.md`.
