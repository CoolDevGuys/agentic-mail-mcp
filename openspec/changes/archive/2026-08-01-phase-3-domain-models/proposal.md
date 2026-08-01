## Why

Phase 2 established shared domain primitives (ValueObject, UUIDId, EventBus, etc.). Phase 3 builds the domain models for all four bounded contexts (Gmail, Intelligence, Search, Notification), defining the core entities, value objects, repository ports, gateway ports, mappers, and domain events that the rest of the system depends on. Without these domain models, no application use cases or infrastructure adapters can be implemented.

## What Changes

- **Gmail domain model**: Email, Thread, Attachment, Label aggregates; EmailAddress, GmailMessageId, ThreadId, HistoryId, GmailQuery value objects; repository ports; GmailGateway anti-corruption layer; domain-to-Gmail API mappers; Gmail-specific domain events
- **Intelligence domain model**: Summary, Classification, Suggestion entities; PromptTemplate, ModelConfig value objects; LlmGateway port
- **Search domain model**: SearchDocument entity; EmbeddingGateway port; VectorSearchRepository port with SearchResult DTO
- **Notification domain model**: ImportantEmailDetected, InboxChanged, DigestReady domain events; NotificationGateway port
- Comprehensive test coverage for all domain artifacts using fakes and the in-memory event bus

## Capabilities

### New Capabilities
- `gmail-domain`: Email, Thread, Attachment, Label aggregates with behaviors, invariants, and factory methods; Gmail-specific value objects (EmailAddress, GmailMessageId, ThreadId, HistoryId, GmailQuery); repository ports; GmailGateway ACL port; mappers; domain events
- `intelligence-domain`: Summary, Classification, Suggestion entities; PromptTemplate and ModelConfig value objects; LlmGateway port for LLM interactions
- `search-domain`: SearchDocument entity with embedding support; EmbeddingGateway port; VectorSearchRepository port with similarity search protocol
- `notification-domain`: Notification-specific domain events (ImportantEmailDetected, InboxChanged, DigestReady); NotificationGateway port for multi-channel notifications

### Modified Capabilities

## Impact

- New modules under `src/Gmail/Domain/`, `src/Intelligence/Domain/`, `src/Search/Domain/`, `src/Notification/Domain/`
- New test modules under `tests/unit/` for each bounded context domain
- New fake implementations in `tests/fakes/` for repository and gateway ports
- Dependencies on Phase 2 primitives (ValueObject, UUIDId, DomainEvent, EventBus, Specification, Clock, IdGenerator)
- No external dependencies beyond what was established in Phase 1 (pyproject.toml)
