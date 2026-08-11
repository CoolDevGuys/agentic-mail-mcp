# Changelog

All notable changes to this project will be documented in this file.

## [0.3.2] - 2026-08-11

### Fixed

- **`search_emails` results now include the full body, recipients, and a usable id.** The per-message fetch behind search used Gmail's `metadata` format, which never returns a body and only carried the headers it was explicitly asked for (not `To`); it now fetches `full` messages instead. Each result's `id` also falls back to the Gmail message id (instead of an empty string) since live search results have no internal cache UUID — the same id `get_email` already accepts.
- **`get_email` no longer loses `date_sent`.** The email cache's mapper parsed the `Date` header with `datetime.fromisoformat`, which raises on real RFC 2822 mail headers (e.g. `"Tue, 11 Aug 2026 10:00:00 +0000"`) and was silently swallowed into `None`; it now parses with `email.utils.parsedate_to_datetime`, matching how search already parsed dates.
- **Forwarded/replied emails no longer drop the original message body.** Body extraction stopped at the first `text/plain` MIME leaf, which is the forward note when the original is nested as a `message/rfc822` attachment; it now concatenates every plain-text leaf (excluding real file attachments) so both the note and the original content come back.
- **`get_thread` is now backed by Gmail instead of a local table nothing ever wrote to.** No code path persisted threads into the local thread cache, so every `get_thread` call raised "not found" in practice. It now calls `users.threads.get` directly and returns every message in the thread with its own full body, sender, recipients, and date — enough to reconstruct the conversation in one call, instead of a list of ids requiring a follow-up `get_email` per message.

## [0.3.1] - 2026-08-09

### Fixed

- **Search and list results now include full message metadata.** `list_messages` fetches subject/from/date/snippet via individual `messages.get` calls after `messages.list`, fixing empty metadata in search results.
- **Cache freshness map is seeded lazily on first access.** Cached list operations no longer return empty results after a server restart, and seeding no longer blocks startup.
- **Database path is validated at startup.** The server exits with a clear error if the DB directory cannot be created or is not writable, instead of failing later with obscure SQLite errors.
- **sqlite_vec extension loads in slim Docker images.** `pysqlite3-binary` is pre-installed and used as the SQLite backend, fixing missing extension loading support on `python:3.11-slim`.
- **Graceful shutdown on SIGTERM.** The CLI installs a signal handler for clean ASGI shutdown via `systemctl stop`.
- **MCP deployment troubleshooting documented.** Configuration docs now cover session ID requirements and common deployment issues.

## [0.2.2] - 2026-08-07

### ⚠ Breaking

- **Renamed the project to `agentic-mail-mcp`.** The distribution name, the
  import package (`src` → `agentic_mail_mcp`), the console command, and the
  environment-variable prefix (`GMAIL_MCP_` → `AGENTIC_MAIL_MCP_`) all changed.
  Update your install, imports, MCP client `command`, and every
  `AGENTIC_MAIL_MCP_*` variable.
- **Running `agentic-mail-mcp` with no subcommand now prints help** instead of
  starting the server. Start it explicitly with `agentic-mail-mcp serve` (update
  MCP client `args`, the Docker `CMD`, and any scripts).
- **Railguards default is now read-only** (Phase 6): `railguards.access_level` defaults to `read_only` (was `owner`), so all write operations (forward/archive/delete/draft) are denied until a deployment sets `AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL=read_write`.

### Fixed

- **Alembic migrations are now packaged.** The migration scripts moved inside the
  `agentic_mail_mcp` package, fixing `agentic-mail-mcp serve` crashing with
  `Path doesn't exist: …/site-packages/migrations` on pip / `uvx` installs (they
  previously resolved only from a source checkout).
- **Deterministic import-order linting across macOS and Linux** (ruff
  `known-first-party` / `known-third-party` pinned), fixing a CI lint failure that
  could not be reproduced or fixed on a case-insensitive filesystem.
- **Environment-variable configuration now works** (Phase 8): the `Settings`
  sub-sections (`gmail`, `database`, `railguards`, `mcp`, `llm`, `search`,
  `notifications`, `logging`) previously ignored their `AGENTIC_MAIL_MCP_<SECTION>_<FIELD>`
  environment variables and always used defaults. Each section now carries its
  own env prefix, so documented variables such as
  `AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL`, `AGENTIC_MAIL_MCP_MCP_TRANSPORT`, and
  `AGENTIC_MAIL_MCP_DATABASE_URL` take effect — required for pip/Docker deployments to
  be configurable.

### Changed

- **Automated PyPI releases** via GitHub Actions using **Trusted Publishing**
  (OIDC — no stored token): publishing a GitHub Release builds and uploads the
  package. `RELEASING.md` was removed in favor of a README section.
- **Expanded documentation**: configuration precedence and the **stdio vs HTTP**
  workflows, the HTTP endpoint URL (`/mcp`), headless / token-copy deployment,
  and the configuration wizard.
- **Caller-first intelligence** ([ADR 0006](specs/docs/adr/0006-caller-first-intelligence.md)):
  the calling agent is itself an LLM, so per-email reasoning (summarize, classify,
  draft reply, extract action items) is now exposed as **MCP prompts** the agent
  runs — no server-side inference, no added latency, and **no LLM key required**
  for the core experience. Internal LLM inference is reserved for the digest tools
  (map-reduce over many emails), which register only when an LLM is configured;
  set `AGENTIC_MAIL_MCP_LLM_INTERNAL_TOOLS=true` to also expose the per-email tools
  server-side. Embeddings for semantic search remain internal.

### Added

- **`init` command** — an interactive wizard that generates a valid `.env`,
  auto-creating the token encryption key, validating input, and backing up any
  existing file (`make init`).
- **`verify-auth` command** — validates the Google client, encryption key, and
  stored token with a **live Gmail call**, printing the authorized account and
  exiting non-zero on failure. The **HTTP server runs the same check at startup**,
  logging a warning (but still starting) when auth is not ready.
- **`--env-file PATH` option** (and the `AGENTIC_MAIL_MCP_ENV_FILE` variable) on
  `serve` / `auth` / `init` — load configuration from (or, for `init`, write it
  to) a specific `.env`, so a client-launched stdio server can be pointed at a
  config file regardless of its working directory.
- **Live write-path smoke test** (`tests/e2e/test_live_write_path.py`, opt-in via
  `AGENTIC_MAIL_MCP_LIVE_WRITE_E2E=1`). Self-contained and safe: it creates its own
  throwaway message and exercises `create_draft` → `send_draft` → `add_label` →
  `forward_email` (to self) → `archive_email` → `delete_email`, then trashes its
  own artifacts. Verified green against a real account. Documented finding:
  permanent delete needs the `https://mail.google.com/` scope (soft delete works
  under `gmail.modify`); `add_label` uses Gmail label **ids** (system labels like
  `STARRED`), not arbitrary user-label names.
- **Bring-your-own Google app** ([ADR 0008](specs/docs/adr/0008-bring-your-own-google-app.md)).
  The server is a local, bring-your-own-credentials tool — no central app, no
  Google verification. Point `AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE` at the
  `credentials.json` you download from your own Google Cloud project (or set the
  client id/secret directly); credentials and token stay on your machine. Docs
  now cover the full self-service Google setup, the unverified-app screen, and
  avoiding the 7-day testing-token expiry.
- **Persistence: read-through cache** ([ADR 0007](specs/docs/adr/0007-persistence-read-through-cache.md)).
  Gmail is the source of truth; local persistence is a `CachedEmailRepository`, not
  a mirror: single-email reads are live (fresh, full body), the SQLite cache stores
  **metadata only — never bodies**, list views are served within a TTL
  (`AGENTIC_MAIL_MCP_DATABASE_CACHE_TTL_SECONDS`, default 900s), and emails gone from the
  server are evicted (no sync engine, no delete-propagation). Tools now identify an
  email by its Gmail **`message_id`** end to end (write commands carry `message_id`;
  the internal UUID is an implementation detail). The Gmail→domain mapper extracts
  bare addresses from display-name headers (`"Name <a@b.com>"`) instead of failing.
- **Runtime composition root + auth** (makes the server usable end to end)
  - `agentic_mail_mcp/Bootstrap/Composition.py` assembles every use case from `Settings` —
    SQLite persistence (schema applied via Alembic), a lazy OAuth-backed Gmail
    gateway, railguard validator, event bus, LLM gateway, and optional semantic
    search — into the `McpUseCases` bundle the server registers. The launched
    `agentic-mail-mcp` now exposes its tools (previously zero).
  - `LazyGmailGateway` builds the authenticated Gmail client on first use, so
    tools register at startup and calls before authorization return a clear
    "run `agentic-mail-mcp auth`" error.
  - `agentic-mail-mcp auth` subcommand performs the one-time interactive Google
    authorization and stores the encrypted token (`make auth`).
  - Semantic search degrades gracefully: `semantic_search` is registered only
    when the `search` extra (sentence-transformers + sqlite-vec) is installed.
- **Distribution and polish** (Phase 8)
  - `LICENSE` (MIT); `pyproject.toml` distribution metadata (`readme`,
    `project.urls`, `license-files`) and a scoped sdist target producing a clean
    source distribution + wheel with the `agentic-mail-mcp` entry point
  - `specs/docs/api.md` — the MCP tool/resource/prompt reference with input
    schemas, output shapes, and the structured error format
  - Architecture ADRs `0002`–`0005` (DDD + vertical slicing, SQLite/PostgreSQL
    persistence, railguards write-safety, MCP stdio transport)
  - Expanded `README.md` (tool catalog, railguards security model, stdio
    integration example, contributing, and the automated PyPI release flow)
  - Multi-stage `Dockerfile` (builder + slim non-root runtime, health check),
    multi-arch build support
  - End-to-end MCP session tests (`tests/e2e/`) covering the read/write tool
    flow, railguard enforcement, and a container health-check smoke test
  - Removed the superseded pre-DDD `main.py` / `server.py` skeletons from the
    repo root (replaced by `agentic_mail_mcp/MCP/Server.py` and `agentic_mail_mcp/Bootstrap/cli.py`)

- **MCP server layer** (Phase 7)
  - `create_server` bootstrap that assembles the server from the dependency container and integrates the application lifespan; configurable transport (`stdio` default, streamable HTTP) via `Settings.mcp.transport`; the `agentic-mail-mcp` console entry point launches it
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
- **Database default is now a synchronous SQLite driver** (`sqlite:///…`) to match the synchronous repository ports (Phase 5). Set `AGENTIC_MAIL_MCP_DATABASE_URL` to a `postgresql+psycopg2://…` URL for PostgreSQL.

### Added (Phase 5 — Infrastructure Adapters)

- **Persistence**: synchronous SQLAlchemy engine/session wiring with a UTC-normalizing datetime type; ORM models and domain↔ORM mappers for Email/Thread/Attachment/Label; `SqliteEmailRepository` / `SqliteThreadRepository`; initial Alembic migration (`alembic.ini` + `migrations/`); PostgreSQL repository variants sharing the schema.
- **Gmail Google adapter**: `GmailOAuthProvider` (Fernet-encrypted token storage), `GmailApiGateway` (Gmail API with retry/backoff and rate limiting), `GmailWatcher` (push notifications + webhook parsing), `GmailHistorySynchronizer` (idempotent history sync emitting domain events).
- **Intelligence**: `LlamaCppGateway` implementing `LlmGateway` over an OpenAI-compatible endpoint or a local llama.cpp model.
- **Search**: `BgeEmbeddingGateway` (`EmbeddingGateway`); `SqliteVecRepository` (default) and `PgVectorRepository` (optional) implementing `VectorSearchRepository`, verified interchangeable by a shared contract test.
- **Notification**: `WebhookNotificationGateway` and `RedisNotificationGateway` implementing `NotificationGateway`.
- **Wiring**: `register_infrastructure()` binds the default adapter stack on the DI container.
- New Settings keys (`llm.base_url`, `llm.model_path`, `search.*`) and optional dependency extras (`postgresql`, `search`, `notifications`, `llm`); see `specs/docs/configuration.md` and `specs/docs/data-model.md`.
