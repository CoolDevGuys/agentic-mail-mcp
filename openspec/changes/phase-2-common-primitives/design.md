## Context

Phase 1 established the project foundation: directory structure, settings, logging, lifespan, DI container, testing infrastructure, Docker, and CI. The directory tree includes empty `Common/Domain/` and `Common/Infrastructure/` folders. Phase 2 populates these with the shared primitives every bounded context depends on.

## Goals / Non-Goals

**Goals:**
- Provide a `ValueObject` base that enforces structural equality, hashing, and repr
- Provide `UUIDId` as the canonical identifier type across all aggregates
- Provide a typed exception hierarchy so callers can distinguish error categories
- Provide an `EventBus` abstraction with an in-memory implementation for tests and lightweight deployments
- Provide a composable `Specification` pattern for query-side business rules
- Provide deterministic `Clock` and `IdGenerator` abstractions for testability

**Non-Goals:**
- External event bus implementations (RabbitMQ, Redis Streams)—those are Phase 5
- Bounded context domain models (Gmail, Intelligence, Search, Notification)—Phases 3+
- Persistence, gateways, or infrastructure adapters

## Decisions

- **ValueObject via dataclass**: `ValueObject` inherits from `dataclasses.dataclass(frozen=True)` to get immutability, `__eq__`, `__hash__`, and `__repr__` for free. Custom `__eq__` compares all fields to ensure value semantics across subclasses.

- **UUIDId wraps `uuid.UUID`**: Not a plain `str`—the `uuid.UUID` type provides validation, formatting, and comparison semantics. `UUIDId` adds a `generate()` class method and ensures the type is distinct from raw UUIDs.

- **Exception hierarchy is flat under `DomainError`**: No deep inheritance tree. All domain exceptions inherit from `DomainError`, which inherits from `Exception`. Each has a `context: dict` for structured error details.

- **EventBus is a Protocol**: Using `typing.Protocol` allows any implementation (in-memory, external) to satisfy the contract without inheritance. `InMemoryEventBus` is synchronous for simplicity; async dispatch is a Phase 5 concern.

- **Specification uses Generic[T]**: `Specification[T]` is typed so `AndSpecification[User]` composes only with other `Specification[User]`. Runtime type checking is not enforced; mypy handles it.

- **Clock returns `datetime`**: `Clock.now()` returns `datetime` (UTC-aware). `TestClock` allows setting arbitrary datetimes for deterministic tests.

- **IdGenerator delegates to UUIDId**: `IdGenerator.generate()` returns `UUIDId`. `UuidIdGenerator` wraps `uuid.uuid4()`. This indirection allows future alternatives (ULID, snowflake) without changing call sites.

## Risks / Trade-offs

- **InMemoryEventBus is synchronous** → external buses will need async support. Mitigation: Protocol defines sync interface; async adapters wrap with `asyncio.to_thread` or provide separate async protocol in Phase 5.
- **Specification pattern adds indirection** → simple queries may overuse it. Mitigation: Reserve for compositional query filters; direct predicates are fine for one-off cases.
