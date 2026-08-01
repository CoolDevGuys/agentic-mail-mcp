## Context

Phase 1 established the project skeleton with empty module stubs. Phase 2 implemented shared domain primitives (ValueObject, UUIDId, DomainEvent, EventBus, Specification, Clock, IdGenerator). The domain layer for all four bounded contexts remains unimplemented, blocking all subsequent phases (application use cases, infrastructure adapters, MCP tools).

The Gmail bounded context is the largest and most complex, requiring four aggregate roots (Email, Thread, Attachment, Label) with rich behavior and invariants. The other contexts (Intelligence, Search, Notification) are simpler but introduce new gateway patterns (LLM, embedding, notification channels).

## Goals / Non-Goals

**Goals:**
- Complete domain models for all four bounded contexts with entities, value objects, ports, and events
- Establish clear aggregate boundaries and invariants
- Define gateway ports (GmailGateway, LlmGateway, EmbeddingGateway, NotificationGateway) as anti-corruption layers
- Define repository ports with complete protocols
- Achieve ≥90% test coverage on all domain code

**Non-Goals:**
- Infrastructure implementations (Google API client, LLM providers, vector databases) — Phase 5
- Application use cases and handlers — Phases 4, 4b, 4c, 4d
- Database persistence and migrations — Phase 5
- MCP tool definitions — Phase 7
- Railguards framework — Phase 6

## Decisions

**1. Email as aggregate root, Thread as separate aggregate**
Email is the primary aggregate with its own lifecycle. Thread is a separate aggregate that references email IDs (not email entities) to maintain loose coupling. This prevents loading entire threads when only a single email is needed, and avoids distributed transaction issues.

**2. GmailGateway as anti-corruption layer (ACL)**
The GmailGateway port translates Gmail API concepts into domain-friendly DTOs. Gateway DTOs use plain dataclasses matching the Gmail API shape, while mappers convert to domain entities. This isolates domain from Gmail API changes.

**3. Value objects for Gmail identifiers**
GmailMessageId, ThreadId, HistoryId are distinct value objects (not plain strings) to prevent mixing identifiers and enable compile-time safety. HistoryId is a string (not int) since Gmail returns it as a string despite being monotonically increasing.

**4. Domain events emitted by aggregates**
Aggregates append domain events to a private `_domain_events` list during behavior execution. The application layer (Phase 4) is responsible for flushing these to the EventBus after persistence. This keeps aggregates decoupled from infrastructure.

**5. System label protection as domain invariant**
The Label entity enforces that system labels (INBOX, SENT, TRASH, etc.) cannot be renamed or deleted. This invariant is checked at the domain level, not just the gateway level.

**6. Intelligence entities as simple entities (not aggregates)**
Summary, Classification, and Suggestion are simple entities without behaviors — they are created by use cases and have no invariants beyond field validation. This keeps the Intelligence context lightweight.

**7. SearchDocument as entity with embedding vector**
The SearchDocument entity stores the embedding vector as a list[float] field. The domain doesn't know about vector databases — that's an infrastructure concern. The VectorSearchRepository port abstracts the storage.

## Risks / Trade-offs

- **Gmail API coupling** → Mitigated by GmailGateway ACL and mappers; domain entities use their own identifiers (UUID) alongside Gmail identifiers
- **Test coverage on mappers** → Gmail API responses are complex nested JSON; will use realistic sample payloads from Gmail API docs
- **Value object validation performance** → EmailAddress RFC 5322 validation is regex-based; acceptable for domain operations (not hot path)
- **Thread aggregate consistency** → Thread only stores email IDs, not entities; eventual consistency with Email aggregates is acceptable since Gmail is the source of truth

## Migration Plan

No migration needed — this is greenfield domain code. All new files follow the project structure established in Phase 1.

## Open Questions

- Should Email.body be lazy-loaded (stored separately) to avoid loading full bodies during search? Decision deferred to Phase 5 (persistence).
- Should Attachment be an aggregate root or part of Email aggregate? Currently modeled as separate entity with reference to email_id. May revisit if attachment lifecycle becomes complex.
