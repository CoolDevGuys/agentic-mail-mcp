## Context

Phase 3 delivered the domain models for the four bounded contexts along with their ports: `EmailRepository`, `ThreadRepository`, `GmailGateway`, `LlmGateway`, `EmbeddingGateway`, `VectorSearchRepository`, and `NotificationGateway`. Phase 2 delivered the shared primitives (`EventBus`/`InMemoryEventBus`, `Clock`, `IdGenerator`, domain exceptions). Fakes for every port already exist under `tests/fakes/`.

The `src/*/Application/` trees are empty stubs. Phase 4 fills them with use cases that orchestrate the domain against those ports. Because all collaborators are ports with existing fakes, the entire application layer is unit-testable with no real infrastructure. Infrastructure implementations (Google API, llama.cpp, sqlite-vss/pgvector, webhook/redis) arrive in Phase 5, and the write path plus railguards arrive in Phase 6.

A subtlety in the implementation plan: Phase 4.2 lists command objects (Forward/Archive/Delete/CreateDraft/SendDraft/AddLabel/MarkRead) but the *handlers* for the write-oriented ones live in Phase 6 with railguard validation, and the MarkRead/AddLabel handlers are simple modify operations. This change therefore delivers the command **data objects** and the **read** use cases, keeping the write execution path out of scope.

## Goals / Non-Goals

**Goals:**
- Implement all read use cases (Gmail), LLM use cases (Intelligence), vector use cases (Search), and event-subscriber use cases (Notification).
- Define query objects, command objects, and DTOs as the stable application-layer contract that Phase 7 MCP tools will consume.
- Establish a consistent use-case shape: constructor injection of ports, a single `execute(input)` method, DTO return values, domain events flushed to the EventBus after work completes.
- Achieve the coverage floors from Phase 1 (≥90% on Domain/, ≥80% overall) for all new application code.

**Non-Goals:**
- Write-path use cases (Forward/Archive/Delete/CreateDraft/SendDraft) and railguard enforcement — Phase 6.
- Any port implementation / real infrastructure — Phase 5.
- MCP tool wiring, resources, prompts — Phase 7.
- The `MarkRead`/`AddLabel` execution handlers — deferred with the other write handlers to Phase 6; only their command objects are defined here.

## Decisions

**1. Use-case shape: injected ports + `execute(input) -> DTO`.**
Each use case is a class taking its collaborators (ports, clock, id generator, event bus) via `__init__`, exposing one async `execute` method that accepts a query/command object and returns a DTO (or DTO list). Rationale: keeps use cases pure orchestration, trivially fakeable, and uniform for the Phase 7 tool layer. Alternative — free functions with explicit args — rejected as it scatters dependency wiring across call sites.

**2. DTOs are plain dataclasses distinct from domain entities.**
`EmailDTO`, `ThreadDTO`, `LabelDTO`, `SummaryDTO`, etc. are serialization-friendly dataclasses, not the domain aggregates. This prevents leaking domain behavior/invariants across the application boundary and gives MCP tools a stable JSON-shaped contract. Mapping entity→DTO lives in the application layer.

**3. Query vs command separation (CQRS-lite).**
Read operations take `*Query` objects and never emit domain events; write operations take `*Command` objects. Phase 4 only executes queries, but defining the command objects now fixes the contract Phase 6 builds on. Alternative — one combined input type — rejected for blurring the read/write boundary the railguards depend on.

**4. SearchEmailsUseCase source is configurable (live API vs local cache).**
Per plan 4.3, the use case can resolve results via `GmailGateway.list_messages()` (live) or `EmailRepository.search()` (cached). A constructor flag/strategy selects the source; default is live API. Rationale: the cache is populated by Phase 5's history synchronizer, so live must work standalone first.

**5. GetEmailUseCase resolves by identifier type with cache-miss fallback.**
A UUID resolves from the local `EmailRepository`; a `GmailMessageId` resolves via the gateway. A local cache miss falls back to the gateway. This matches plan 4.4 and keeps a single entry point for both identifier kinds.

**6. Domain events flushed by the use case after the operation.**
Consistent with the Phase 3 decision that aggregates append to `_domain_events` and the application layer publishes them. Read use cases publish nothing; Intelligence's digest use cases publish `DigestReady`; Notification use cases are themselves subscribers that react to already-published events.

**7. Notification use cases are event subscribers, not request/response.**
`NotifyImportantEmailUseCase` subscribes to `ImportantEmailDetected` and `PublishInboxEventUseCase` subscribes to inbox-change events, each dispatching through `NotificationGateway`. They register their handlers on the `EventBus` at construction/wiring time. Tests publish events on the in-memory bus and assert gateway calls.

**8. LLM prompt construction via Phase 3 PromptTemplate.**
Intelligence use cases build prompts from `PromptTemplate` value objects rather than inline f-strings, so prompts are testable and reusable. Each use case persists its result entity (Summary/Classification/Suggestion) via the relevant repository before returning the DTO.

## Risks / Trade-offs

- **Ambiguous read/write boundary for AddLabel/MarkRead** → Their command objects are defined here but execution handlers deferred to Phase 6; documented explicitly so Phase 6 doesn't redefine the commands.
- **Digest time-window semantics** → Daily/weekly digests depend on `Clock` and unread/important queries; use injected `Clock` (Phase 2 `TestClock` in tests) to keep time filtering deterministic.
- **DTO drift from entities** → Duplicating fields in DTOs risks divergence; mitigated by mapping functions covered by unit tests, and by keeping DTOs thin (no behavior).
- **SemanticSearch/embedding dimension mismatch** → `EmbeddingGateway.dimension()` must match indexed vectors; use cases assert/normalize before search, exercised against `FakeEmbeddingGateway`.

## Migration Plan

Greenfield application code filling existing empty stubs; no data migration. New files follow the Phase 1 project structure. No changes to Phase 3 domain modules or ports. Delivered incrementally per bounded context (Gmail → Intelligence → Search → Notification), each context independently testable.

## Open Questions

- Should `SearchEmailsUseCase` expose the live/cache toggle as a per-request query field or a construction-time strategy? Leaning construction-time; revisit if Phase 7 needs per-call control.
- Digest DTO grouping shape (by sender vs by category) — defer concrete grouping to the LLM prompt output; DTO stays a list of grouped summary blocks.
