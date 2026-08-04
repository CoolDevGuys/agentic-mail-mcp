# Implementation Plan - Gmail MCP Server

> Full V1 scope: Gmail, Intelligence, Search, Notification bounded contexts.
> Persistence: SQLite default, PostgreSQL optional.
> Distribution: PyPI package + Docker image.

## Scope Notes (V1)
- **Email filtering (Gmail filter rules)** — creating/managing server-side Gmail auto-filters (auto-label, auto-archive incoming mail) is explicitly out of scope for V1. `SearchEmailsQuery` / `GmailQuery` (Phase 4.1, 3.2) cover ad-hoc *search* filtering criteria only, not persistent filter rules. Revisit as a V2 candidate if needed.

---

## Phase 1 - Project Foundation [DONE]

### 1.1 - pyproject.toml
Create a complete pyproject.toml with:
- Project metadata (name: gmail-mcp-server, version, description, authors)
- Build system: hatchling
- Dependencies: mcp, google-api-python-client, google-auth-oauthlib, pydantic, pydantic-settings, aiosqlite, asyncpg (optional), sqlalchemy, alembic, httpx, python-dotenv
- Optional extras: [postgresql] for asyncpg + psycopg2, [dev] for pytest, pytest-asyncio, pytest-cov, ruff, mypy
- Entry point: console script gmail-mcp-server pointing to the MCP server CLI
- Classifiers: Python 3.11+

### 1.2 - Bootstrap src/ folder structure
Create the full directory tree per specs/docs/project_structure.md:
- src/Bootstrap/ with __init__.py and empty stubs for each module
- src/Common/Domain/ValueObjects/, Exceptions/, Events/, Specifications/, Repository/
- src/Common/Infrastructure/Persistence/Migrations/, Messaging/, LLM/, Clock/, IdGenerator/
- src/Gmail/Domain/Entities/, ValueObjects/, Repository/, Gateway/, Mapper/, Events/
- src/Gmail/Application/UseCases/, DTO/, Commands/, Queries/, Handlers/
- src/Gmail/Infrastructure/Google/, Persistence/SqlAlchemy/Models/, Repositories/, Mappers/, Persistence/PostgreSQL/, MCP/
- src/Intelligence/Domain/Entities/, Repository/, Gateway/, ValueObjects/
- src/Intelligence/Application/UseCases/, DTO/
- src/Intelligence/Infrastructure/LlamaCpp/
- src/Search/Domain/Repository/, Gateway/, Entities/
- src/Search/Application/UseCases/
- src/Search/Infrastructure/PgVector/, BGE/
- src/Notification/Domain/Gateway/, Events/
- src/Notification/Application/UseCases/
- src/Notification/Infrastructure/RabbitMQ/, Redis/, Webhook/
- src/MCP/ with __init__.py and stubs for Server.py, ToolRegistry.py, Resources.py, Prompts.py, Tools/
- All directories get __init__.py
### 1.3 - Bootstrap/Settings.py
Implement a pydantic-settings based configuration layer. This is the single configuration entry point for the project (supersedes the separate `Configuration.py` originally sketched in `project_structure.md`, which has been removed to avoid two competing config-loading paths):
- Settings class inheriting from pydantic_settings.BaseSettings
- Sections: gmail (OAuth client ID/secret, scopes, token_storage_path, token_encryption_key), database (URL, driver), railguards (access_level, allowed recipients, blocked actions, rate limits), mcp (server name, host, port), llm (provider, model, API key), notifications (webhook URL, Redis URL)
- Supports .env file and environment variables with prefix GMAIL_MCP_
- Settings.from_env() class method as factory
- .env.example with all keys documented, no real secrets

### 1.4 - Bootstrap/Logging.py
Implement structured JSON logging:
- setup_logging(level, json_format) function
- JSON formatter with correlation_id, timestamp, level, module, message
- Redaction filter: masks values matching patterns for tokens, passwords, email bodies
- Configurable via Settings.logging.level

### 1.5 - Bootstrap/Lifespan.py
Implement async application lifespan:
- async def lifespan(app) context manager
- Startup: initialize DB connection pool, warm OAuth token, register domain event handlers
- Shutdown: close DB connections, flush audit log, unsubscribe from Gmail push notifications
- Integrates with MCP server lifecycle

### 1.6 - Bootstrap/DependencyContainer.py
Implement a simple DI container:
- Container class with register(), resolve(), singleton() methods
- Supports factory functions and async factories
- No heavy framework; just a dict-based resolver with type hints
- Pre-registered services: settings, logger, DB session factory, event bus

### 1.7 - Testing infrastructure
Set up:
- pytest.ini with asyncio_mode = auto, testpaths, markers
- tests/conftest.py with shared fixtures: settings, event_bus, clock, container
- tests/unit/ and tests/integration/ directories
- tests/fakes/ directory for in-memory fakes: FakeEmailRepository, FakeGmailGateway, FakeLlmGateway, FakeEmbeddingGateway, FakeNotificationGateway
- pytest-cov config targeting src/ with a tiered floor: ≥90% on Domain/, ≥80% overall; CI fails the build below either floor

### 1.8 - Docker setup
- Dockerfile: Python 3.11 slim base, copy pyproject.toml, install deps, copy source, run as non-root user
- docker-compose.yml: gmail-mcp-server service + postgres service (optional, for PG testing)
- Health check on MCP server port
- .dockerignore excluding .venv, __pycache__, .git

### 1.9 - CI/CD pipeline
- GitHub Actions workflow: lint (ruff), type-check (mypy), test (pytest with coverage) on every push/PR
- Dependency vulnerability scanning (e.g., pip-audit or GitHub Dependabot) on a schedule and on dependency changes
- Lockfile committed to the repo (matching the chosen build tool) and validated in CI
- Build/publish job gated on CI green, triggered on release tag
- Tests: CI config validated by running it; no application tests needed here

---

## Phase 2 - Common Module (Shared Primitives) [DONE]

### 2.1 - Common/Domain/ValueObjects/
- base.py: abstract ValueObject with __eq__, __hash__, __repr__ based on all attributes
- uuid_id.py: UUIDId value object wrapping uuid.UUID, with generate() class method
- Tests: equality, hashing, repr, UUID generation

### 2.2 - Common/Domain/Exceptions/
- DomainError (base, message, context dict)
- ValidationError (for value object and entity validation failures)
- NotFoundError (entity not found by ID)
- PermissionError (railguard or authorization failures)
- ConcurrencyError (optimistic lock failures)
- Tests: exception instantiation, message propagation

### 2.3 - Common/Domain/Events/
- DomainEvent base: event_id (UUID), occurred_at (datetime), aggregate_id
- EventBus protocol: publish(event), subscribe(event_type, handler), publish_all(events)
- InMemoryEventBus: in-memory implementation for tests and lightweight deployments
- Tests: publish/subscribe flow, multiple handlers, event ordering

### 2.4 - Common/Domain/Specifications/
- Specification[T] base with is_satisfied_by(candidate) abstract method
- AndSpecification, OrSpecification, NotSpecification composables
- Tests: composition logic, chained specifications

### 2.5 - Common/Infrastructure/Clock/
- Clock protocol: now() -> datetime
- SystemClock: wraps datetime.now(timezone.utc)
- TestClock: injectable, settable time for deterministic tests
- Tests: system clock returns UTC, test clock returns set time

### 2.6 - Common/Infrastructure/IdGenerator/
- IdGenerator protocol: generate() -> UUIDId
- UuidIdGenerator: wraps uuid.uuid4()
- Tests: uniqueness, type correctness---

## Phase 3 - Gmail Bounded Context: Domain [DONE]

### 3.1 - Gmail/Domain/ValueObjects/EmailAddress.py
- EmailAddress VO with RFC 5322 validation (local-part@domain)
- Properties: local_part, domain
- Validation: non-empty, valid format, max 254 chars
- Tests: valid emails, invalid formats, edge cases (subdomains, plus addressing)

### 3.2 - Gmail-specific Value Objects
- GmailMessageId: wraps Gmail string message ID, immutable
- ThreadId: wraps Gmail thread ID
- HistoryId: wraps Gmail history ID (monotonically increasing string)
- GmailQuery: wraps a Gmail search query string; validates non-empty, max length; provides builders for common queries (from_sender, with_subject, date_range, has_attachment, label, unread)
- Tests: each VO for validation, immutability; GmailQuery builders compose correctly

### 3.3 - Gmail/Domain/Entities/Email.py
- Email aggregate root with: id (UUID), message_id (GmailMessageId), thread_id (ThreadId), snippet, subject, from_address, to_addresses, date_sent, is_read, labels, body, attachments, _domain_events
- Factory: Email.from_gmail_message(gmail_data) creates from API response via mapper
- Behaviors: mark_read(), add_label(label), remove_label(label), archive(), move_to_trash(), restore_from_trash()
- Invariants: cannot restore a message not in trash; labels are unique set
- Tests: factory, all behaviors, invariants, domain event emission

### 3.4 - Gmail/Domain/Entities/Thread.py
- Thread aggregate: id (UUID), thread_id (ThreadId), snippet, subject, participants, email_ids (ordered list), last_updated, is_read
- Behaviors: add_email(email_id), mark_read(), add_label(), archive(), move_to_trash()
- Invariants: emails ordered by date; thread cannot be empty
- Tests: behaviors, invariants, multi-email thread operations

### 3.5 - Gmail/Domain/Entities/Attachment.py
- Attachment entity: id (UUID), file_name, mime_type, size_bytes, attachment_id (Gmail ID), download_url
- Value object: AttachmentMetadata (name, type, size)
- Tests: entity creation, metadata validation

### 3.6 - Gmail/Domain/Entities/Label.py
- Label entity: id (UUID), label_id (Gmail ID), name, color, type (system/user)
- Behaviors: rename(new_name)
- Invariants: system labels cannot be renamed or deleted
- Tests: creation, rename, system label protection
### 3.7 - Repository Ports
- EmailRepository protocol: find_by_id(id), find_by_gmail_message_id(message_id), find_by_thread_id(thread_id), search(query), list_unread(limit), save(email), delete(id)
- ThreadRepository protocol: find_by_id(id), find_by_gmail_thread_id(thread_id), save(thread), delete(id)
- Tests: protocol contracts via fakes

### 3.8 - Gmail/Domain/Gateway/GmailGateway.py
- GmailGateway anti-corruption layer port with methods:
  - list_messages(query, page_token, max_results) -> GmailListResponse
  - get_message(message_id, format) -> GmailMessage
  - get_batch_messages(message_ids) -> list[GmailMessage]
  - send_message(raw_message) -> SentMessageResult
  - modify_message(message_id, add_labels, remove_labels) -> ModifyResult
  - trash_message(message_id), untrash_message(message_id)
  - delete_message(message_id)
  - list_labels() -> list[GmailLabel]
  - watch(notification_url, webhook_token) -> WatchResponse
  - stop_watch() -> StopWatchResult
  - get_history(history_id, start_history_id) -> GmailHistory
  - download_attachment(message_id, attachment_id) -> bytes
- Gateway DTOs as plain dataclasses (Gmail API shape, not domain entities)
- Tests: none (interface only); tested via infrastructure implementation

### 3.9 - Mappers
- EmailMapper.to_domain(gateway_message) -> Email
- ThreadMapper.to_domain(gateway_thread) -> Thread
- Handle field mapping, type conversion, nested payloads
- Tests: mapper correctness with sample Gmail API responses

### 3.10 - Domain Events
- EmailReceived(email_id, from_address, subject, received_at)
- EmailArchived(email_id, archived_at)
- EmailDeleted(email_id, deleted_at)
- EmailForwarded(email_id, forwarded_to, forwarded_at)
- EmailLabeled(email_id, label_name, labeled_at)
- InboxSynchronized(history_id, synchronized_at, email_count)
- Tests: event instantiation, required fields; use-case-level tests (Phase 4/6) assert each event is published to the EventBus with the correct payload via the in-memory bus---

## Phase 3b - Intelligence Bounded Context: Domain [DONE]

### 3b.1 - Intelligence Entities
- Summary: id, email_id, summary_text, model_used, created_at
- Classification: id, email_id, category (urgent/normal/spam/promo), priority (1-5), confidence, model_used, created_at
- Suggestion: id, email_id, suggestion_type (reply/forward/ignore), draft_text, model_used, created_at
- Tests: entity creation, field validation

### 3b.2 - Intelligence/Domain/Gateway/LlmGateway.py
- LlmGateway port: generate(prompt, system_prompt, max_tokens, model) -> LlmResponse
- LlmResponse: text, model, usage (input_tokens, output_tokens)
- Tests: none (interface only)

### 3b.3 - Intelligence Value Objects
- PromptTemplate: name, template string with {variable} placeholders; render(**kwargs) -> str
- ModelConfig: provider, model_id, max_tokens, temperature
- Tests: template rendering, config validation

---

## Phase 3c - Search Bounded Context: Domain [DONE]

### 3c.1 - Search Entities
- SearchDocument: id, email_id, content (text to index), embedding (vector), metadata (subject, sender, date)
- Tests: entity creation

### 3c.2 - Search/Domain/Gateway/EmbeddingGateway.py
- EmbeddingGateway port: embed(text) -> list[float], dimension() -> int
- Tests: none (interface only)

### 3c.3 - Search Repository Port
- VectorSearchRepository protocol: index(document), search(query_vector, limit, min_score) -> list[SearchResult], delete(email_id), count() -> int
- SearchResult: document_id, email_id, score, metadata
- Tests: protocol via fake

---

## Phase 3d - Notification Bounded Context: Domain [DONE]

### 3d.1 - Notification Events
- ImportantEmailDetected(email_id, from_address, subject, priority, detected_at)
- InboxChanged(event_type, email_id, changed_at)
- DigestReady(digest_type, digest_period, email_count, generated_at)
- Tests: event instantiation

### 3d.2 - Notification/Domain/Gateway/NotificationGateway.py
- NotificationGateway port: send(title, body, channel) -> bool, publish(event_type, payload) -> bool
- Tests: none (interface only)---

## Phase 4 - Gmail Application: Use Cases [DONE]

### 4.1 - Query Objects
- SearchEmailsQuery: query_string, from_address, to_address, subject, date_from, date_to, has_attachment, label, unread_only, page, page_size
- GetEmailQuery: email_id (UUID or GmailMessageId)
- GetThreadQuery: thread_id
- ListUnreadQuery: limit, label
- ListLabelsQuery: label_type (system/user/all)
- Tests: query validation

### 4.2 - Command Objects
- ForwardEmailCommand: email_id, to_address, subject, body, include_original
- ArchiveEmailCommand: email_id (or thread_id)
- DeleteEmailCommand: email_id, permanent (bool, default False)
- CreateDraftCommand: to_address, subject, body, attachments
- SendDraftCommand: draft_id
- AddLabelCommand: email_id, label_name
- MarkReadCommand: email_id
- Tests: command validation

### 4.3 - SearchEmailsUseCase
- Accepts SearchEmailsQuery
- Builds GmailQuery from query criteria
- Calls GmailGateway.list_messages() or EmailRepository.search() (configurable: live API vs cached)
- Returns SearchEmailsResult: paginated list of EmailDTO
- Handles: empty results, pagination, query errors
- Tests: various query combinations, pagination, error handling

### 4.4 - GetEmailUseCase / GetThreadUseCase
- GetEmailUseCase: resolves by UUID (local cache) or GmailMessageId (live API), returns EmailDTO with body
- GetThreadUseCase: resolves thread with all email IDs, returns ThreadDTO
- Tests: happy path, not found, cache miss fallback to API

### 4.5 - ListUnreadUseCase
- Returns paginated list of unread EmailDTOs
- Optional label filter
- Tests: with/without label filter, pagination

### 4.6 - ListLabelsUseCase
- Returns list of LabelDTOs
- Filters by type (system, user, all)
- Tests: all filter types

### 4.7 - Unit tests for all read use cases---

## Phase 4b - Intelligence Application [DONE]

### 4b.1 - SummarizeEmailUseCase
- Accepts email_id, calls LlmGateway with summarization prompt
- Persists Summary entity
- Returns SummaryDTO
- Tests: with fake LLM, persistence verification

### 4b.2 - SuggestReplyUseCase
- Accepts email_id, calls LLM with reply suggestion prompt
- Persists Suggestion entity
- Returns SuggestionDTO
- Tests: with fake LLM

### 4b.3 - ClassifyEmailUseCase
- Accepts email_id, calls LLM with classification prompt
- Persists Classification entity
- Returns ClassificationDTO with category and priority
- Tests: all categories, confidence thresholds

### 4b.4 - DailyDigestUseCase / WeeklyDigestUseCase
- Queries unread/important emails for time period
- Calls LLM to generate digest summary
- Returns DigestDTO with grouped summaries
- Publishes DigestReady event
- Tests: time filtering, LLM integration, event emission

### 4b.5 - ExtractActionItemsUseCase
- Accepts email_id, calls LLM to extract action items
- Returns list of ActionItemDTO (description, due_date, priority)
- Tests: extraction accuracy with fake LLM

### 4b.6 - Unit tests for all Intelligence use cases

---

## Phase 4c - Search Application [DONE]

### 4c.1 - SemanticSearchUseCase
- Accepts natural language query
- Calls EmbeddingGateway to vectorize query
- Calls VectorSearchRepository for similarity search
- Returns list of SearchResultDTO with scores
- Tests: with fake embedding and vector repo

### 4c.2 - IndexEmailUseCase
- Accepts email_id
- Extracts indexable text from email
- Calls EmbeddingGateway to create embedding
- Persists SearchDocument via VectorSearchRepository
- Tests: text extraction, embedding, persistence

### 4c.3 - RebuildIndexUseCase
- Iterates all indexed emails
- Re-embeds and re-indexes each
- Returns rebuild statistics
- Tests: full rebuild flow with fake data

### 4c.4 - Unit tests for all Search use cases---

## Phase 4d - Notification Application [DONE]

### 4d.1 - NotifyImportantEmailUseCase
- Subscribes to ImportantEmailDetected domain event
- Calls NotificationGateway.send() with appropriate channel
- Tests: event handling, notification dispatch

### 4d.2 - PublishInboxEventUseCase
- Subscribes to inbox change domain events
- Publishes to external notification channels via NotificationGateway
- Tests: event routing, multi-channel publishing

### 4d.3 - Unit tests for all Notification use cases

---

## Phase 5 - Infrastructure Adapters [DONE]

### 5.1 - Gmail/Infrastructure/Google/ (OAuth, API Gateway, Watcher)
- GmailOAuthProvider: OAuth2 flow (interactive browser + headless with pre-authorized tokens); persists refresh tokens outside the repo (path from Settings.gmail.token_storage_path, default outside the project directory e.g. ~/.config/gmail-mcp-server/), encrypted at rest using Settings.gmail.token_encryption_key; never logs token values (relies on Bootstrap/Logging.py redaction filter, 1.4)
- GmailApiGateway: implements GmailGateway port using google-api-python-client; wraps all API calls with retry logic and rate limiting
- GmailWatcher: manages Gmail push notifications (watch/stop-watch); processes webhook callbacks
- GmailHistorySynchronizer: processes history changes, updates local cache, emits domain events
- Tests: mocked HTTP layer for all gateway methods

### 5.2 - Gmail/Infrastructure/Persistence/SqlAlchemy/ (SQLite default)
- SqlAlchemy models: Email, Thread, Attachment, Label mapped to tables
- SqlAlchemy repositories: SqliteEmailRepository, SqliteThreadRepository implementing repository ports
- Domain-to-ORM mappers
- Alembic migration: initial schema creation; alembic.ini at repo root; single migrations/ directory shared across SQLite/PostgreSQL
- Tests: integration tests with in-memory SQLite

### 5.3 - Gmail/Infrastructure/Persistence/PostgreSQL/ (optional)
- PG-specific repository implementations with asyncpg driver
- PG-specific migration scripts
- Tests: integration tests with dockerized PostgreSQL

### 5.4 - Intelligence/Infrastructure/LlamaCpp/LlamaCppGateway.py
- Implements LlmGateway port using llama.cpp or OpenAI-compatible API
- Configurable via Settings: local model path or remote API endpoint
- Tests: mocked LLM responses

### 5.5 - Search/Infrastructure/SqliteVSS/, PgVector/, and BGE/
- SqliteVSS adapter (default, matches the project-wide SQLite default): stores and queries embeddings via sqlite-vss; implements VectorSearchRepository port
- PgVector adapter (optional, requires PostgreSQL): stores and queries embeddings via pgvector extension; implements the same port
- BGE embedding provider: calls BGE model to generate text embeddings, shared by both adapters
- Tests: integration with both backends; VectorSearchRepository contract tests run against both adapters to guarantee interchangeability

### 5.6 - Notification/Infrastructure/Webhook/ and Redis/
- Webhook adapter: POSTs notification payloads to configured URLs
- Redis adapter: pub/sub for real-time event distribution
- Tests: mocked HTTP for webhooks, fakeredis for Redis

### 5.7 - Integration tests for all infrastructure adapters---

## Phase 6 - Railguards Framework [DONE]

### 6.1 - Railguard configuration model
- AccessLevel: read_only (default) or read_write — the single top-level switch gating whether any write capability exists at all
- AllowedRecipients: list of email addresses/domains allowed for forwarding
- BlockedActions: list of actions blocked by default (e.g., permanent_delete)
- RateLimits: max operations per time window (e.g., 50 forwards/hour)
- ArchiveFirstPolicy: require archive before delete
- Configurable via Settings.railguards section
- Tests: configuration parsing, validation, default is read_only when unset

### 6.2 - RailguardValidator
- Validates commands against railguard rules before execution
- Checks: recipient allowlist, action blocklist, rate limits, archive-first policy
- Returns RailguardResult: allowed/denied with reason
- Throws PermissionError on violation
- Tests: all rule combinations, edge cases

### 6.3 - Audit log infrastructure
- AuditLog entry: timestamp, action, email_id, details, correlation_id
- AuditLogRepository: persists audit entries
- AuditLogHandler: domain event subscriber that logs all write operations
- Tests: audit trail completeness, correlation IDs

### 6.4 - ForwardEmailUseCase (with railguards)
- Validates recipient against allowlist
- Checks rate limit
- Builds forwarded message with original as RFC822 attachment
- Calls GmailGateway.send_message()
- Emits EmailForwarded event
- Tests: allowed recipient (asserts EmailForwarded published to event bus with correct payload), blocked recipient, rate limit exceeded

### 6.5 - ArchiveEmailUseCase (with railguards)
- Validates action not blocked
- Removes INBOX label via GmailGateway.modify_message()
- Emits EmailArchived event
- Tests: single email, thread archive, blocked action; asserts EmailArchived published to event bus with correct payload

### 6.6 - DeleteEmailUseCase (with railguards)
- Validates archive-first policy (email must be archived before permanent delete)
- Soft delete (trash) by default; permanent delete only if command.permanent=True and not blocked
- Emits EmailDeleted event
- Tests: soft delete, permanent delete blocked, archive-first enforcement; asserts EmailDeleted published to event bus with correct payload

### 6.7 - CreateDraftUseCase (draft-first sending)
- Creates draft via GmailGateway without sending
- Returns draft_id for human review
- SendDraftCommand sends the reviewed draft
- Tests: draft creation, draft sending, draft deletion

### 6.8 - Unit and integration tests for all railguard scenarios---

## Phase 7 - MCP Server Layer [DONE]

### 7.1 - MCP/Server.py
- MCP server bootstrap with DI integration
- Configurable transport: stdio (default for AI agents) or HTTP
- Lifespan integration with Bootstrap/Lifespan.py
- Tests: server starts and stops cleanly

### 7.2 - MCP/ToolRegistry.py
- Tool registration with AI-agent-friendly descriptions
- Each tool: name, description, input schema (JSON Schema), handler function
- Groups tools by category: read, write, intelligence, search
- Defense-in-depth: reads Settings.railguards.access_level at registration time and skips registering any write-category tool when access_level is read_only, so write tools are never exposed to the agent at all — not just blocked at execution time by RailguardValidator (Phase 6.2)
- Tests: all tools registered when read_write, write tools absent from the registry when read_only, schemas valid

### 7.3 - Read Tools
- SearchEmailsTool: wraps SearchEmailsUseCase; params: query, from, to, subject, date range, label, unread, page, page_size
- GetEmailTool: wraps GetEmailUseCase; params: email_id
- GetThreadTool: wraps GetThreadUseCase; params: thread_id
- ListUnreadTool: wraps ListUnreadUseCase; params: limit, label
- ListLabelsTool: wraps ListLabelsUseCase; params: label_type
- Tests: tool-to-use-case wiring, parameter validation

### 7.4 - Write Tools (with railguards)
- ForwardEmailTool: wraps ForwardEmailUseCase; params: email_id, to, subject, body, include_original
- ArchiveEmailTool: wraps ArchiveEmailUseCase; params: email_id or thread_id
- DeleteEmailTool: wraps DeleteEmailUseCase; params: email_id, permanent
- CreateDraftTool: wraps CreateDraftUseCase; params: to, subject, body
- SendDraftTool: wraps SendDraftUseCase; params: draft_id
- AddLabelTool: wraps AddLabelUseCase; params: email_id, label
- Tests: railguard enforcement at tool level

### 7.5 - Intelligence Tools
- SummarizeEmailTool: wraps SummarizeEmailUseCase; params: email_id
- ClassifyEmailTool: wraps ClassifyEmailUseCase; params: email_id
- SuggestReplyTool: wraps SuggestReplyUseCase; params: email_id
- ExtractActionItemsTool: wraps ExtractActionItemsUseCase; params: email_id
- DailyDigestTool: wraps DailyDigestUseCase; params: date
- WeeklyDigestTool: wraps WeeklyDigestUseCase; params: week_start
- Tests: LLM integration via tools

### 7.6 - Search Tools
- SemanticSearchTool: wraps SemanticSearchUseCase; params: query, limit, min_score
- Tests: semantic search via tool

### 7.7 - MCP/Resources.py
- Account info resource: connected account details, access level
- Watch status resource: Gmail push notification status
- Index status resource: vector search index statistics
- Tests: resource availability

### 7.8 - MCP/Prompts.py
- Pre-built prompts to help AI agents use the MCP server effectively
- Example: search strategy prompt, email management workflow prompt
- Tests: prompt rendering---

## Phase 8 - Distribution and Polish [DONE]

### 8.1 - README.md
- Project description, architecture overview
- Installation: pip install and docker methods
- Configuration: all environment variables with examples
- Usage: AI agent integration examples (stdio transport)
- Available tools: complete list with descriptions
- Railguards: configuration guide and security model
- Contributing guidelines

### 8.2 - Specs/docs/api.md
- Complete MCP tools documentation: name, description, input schema, output schema
- MCP resources documentation
- MCP prompts documentation
- Error response formats

### 8.3 - Specs/docs/domain-model.md
- Bounded context diagram
- Entity relationships
- Value objects catalog
- Domain events catalog
- Aggregate boundaries

### 8.4 - specs/docs/configuration.md
- Every environment variable / Settings field documented: name, purpose, default, required vs optional
- Sections mirroring Settings structure: gmail, database, railguards, mcp, llm, notifications
- Kept in sync with .env.example

### 8.5 - specs/docs/adr/
- ADR 0001: DDD + vertical slicing architecture (why bounded contexts over layered/technical folders)
- ADR 0002: SQLite default / PostgreSQL optional persistence strategy
- ADR 0003: Railguards model for write-access safety (read-only-by-default access level, allowlist, rate limits, archive-first policy)
- ADR 0004: MCP stdio transport as default distribution mechanism for AI agent harnesses
- Each ADR follows the template in specs/guidelines/documentation-standards.md (Status, Context, Decision, Consequences)

### 8.6 - PyPI packaging
- pyproject.toml with complete build configuration
- License file (MIT or Apache 2.0)
- Console script entry point: gmail-mcp-server
- Test PyPI publish (test.pypi.org)
- Production PyPI publish

### 8.7 - Docker multi-stage build
- Builder stage: install deps, build package
- Runtime stage: slim Python image, copy built package
- Non-root user, read-only filesystem where possible
- Health check endpoint
- Multi-arch build (amd64, arm64)

### 8.8 - E2E tests
- Full MCP session with mocked Gmail API (wiremock or pytest-httpserver)
- Tool invocation flow: search, read, forward, archive, delete
- Railguard enforcement in E2E context
- Docker container startup and health check

### 8.9 - Cleanup
- Move main.py to examples/legacy/ or remove
- Remove token.json, credentials.json from repo (add to .gitignore, along with the default token_storage_path from 5.1)
- Remove server.py skeleton (replaced by MCP/Server.py)
- Final lint and type-check pass
- Verify all tests pass (unit + integration + E2E)

---

## Summary

Total tasks: ~98 across 8 phases.

| Phase | Tasks | Focus |
|---|---|---|
| 1 | 9 | Project foundation, tooling, Docker, CI/CD |
| 2 | 6 | Shared domain primitives |
| 3 | 10 | Gmail domain model |
| 3b | 3 | Intelligence domain model |
| 3c | 3 | Search domain model |
| 3d | 2 | Notification domain model |
| 4 | 7 | Gmail application use cases |
| 4b | 6 | Intelligence application use cases |
| 4c | 4 | Search application use cases |
| 4d | 3 | Notification application use cases |
| 5 | 7 | Infrastructure adapters |
| 6 | 8 | Railguards + safe write use cases |
| 7 | 8 | MCP server layer |
| 8 | 9 | Distribution, docs, polish |
