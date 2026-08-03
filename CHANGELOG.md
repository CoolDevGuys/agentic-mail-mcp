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
