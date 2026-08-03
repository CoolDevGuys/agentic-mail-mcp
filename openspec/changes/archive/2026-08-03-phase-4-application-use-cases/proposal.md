## Why

Phase 3 completed the domain models for all four bounded contexts (Gmail, Intelligence, Search, Notification), but those entities, ports, and events have no callers yet. Phase 4 builds the application layer — the use cases that orchestrate the domain to fulfil real tasks (searching mail, summarizing, semantic search, notifications). Without this layer there is nothing for the Phase 5 infrastructure adapters and Phase 7 MCP tools to wire into.

## What Changes

- **Gmail application (Phase 4)**: read-side query objects (SearchEmailsQuery, GetEmailQuery, GetThreadQuery, ListUnreadQuery, ListLabelsQuery), the full command-object catalog (ForwardEmailCommand, ArchiveEmailCommand, DeleteEmailCommand, CreateDraftCommand, SendDraftCommand, AddLabelCommand, MarkReadCommand), read DTOs (EmailDTO, ThreadDTO, LabelDTO), and the read use cases: SearchEmailsUseCase, GetEmailUseCase, GetThreadUseCase, ListUnreadUseCase, ListLabelsUseCase.
- **Intelligence application (Phase 4b)**: SummarizeEmailUseCase, SuggestReplyUseCase, ClassifyEmailUseCase, DailyDigestUseCase, WeeklyDigestUseCase, ExtractActionItemsUseCase, with SummaryDTO, SuggestionDTO, ClassificationDTO, DigestDTO, ActionItemDTO.
- **Search application (Phase 4c)**: SemanticSearchUseCase, IndexEmailUseCase, RebuildIndexUseCase, with SearchResultDTO.
- **Notification application (Phase 4d)**: NotifyImportantEmailUseCase and PublishInboxEventUseCase as domain-event subscribers dispatching through NotificationGateway.
- Comprehensive unit tests for every use case using the existing fakes (FakeEmailRepository, FakeGmailGateway, FakeLlmGateway, FakeEmbeddingGateway, FakeNotificationGateway) and the in-memory event bus.

Note: the **write** use cases (Forward/Archive/Delete/CreateDraft/SendDraft) are intentionally deferred to Phase 6, where they are implemented together with the railguards framework. Phase 4 defines their *command objects* only so the read layer and DTOs are complete.

## Capabilities

### New Capabilities
- `gmail-application`: Query and command objects, read DTOs, and read-side use cases (search, get email, get thread, list unread, list labels) that orchestrate the Gmail domain and GmailGateway/EmailRepository ports.
- `intelligence-application`: LLM-backed use cases (summarize, suggest reply, classify, daily/weekly digest, extract action items) that call LlmGateway, persist Intelligence entities, and return DTOs.
- `search-application`: Semantic search, index-email, and rebuild-index use cases coordinating EmbeddingGateway and VectorSearchRepository.
- `notification-application`: Domain-event-subscriber use cases that route important-email and inbox-change events to external channels via NotificationGateway.

### Modified Capabilities
<!-- None. Phase 4 consumes the domain ports defined in Phase 3 without changing their requirements. -->

## Impact

- New modules under `src/Gmail/Application/` (Queries, Commands, DTO, UseCases), `src/Intelligence/Application/` (UseCases, DTO), `src/Search/Application/UseCases/`, and `src/Notification/Application/UseCases/` — all currently empty stubs.
- New unit-test modules under `tests/unit/` for each bounded context's application layer.
- Depends on Phase 3 domain models (entities, repository/gateway ports, domain events) and Phase 2 primitives (EventBus, Clock, IdGenerator, exceptions).
- No new external dependencies beyond those already declared in Phase 1's pyproject.toml.
- Write-path use cases and railguard enforcement are out of scope (Phase 6); infrastructure adapters that implement the ports are out of scope (Phase 5).
