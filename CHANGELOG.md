# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added

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
