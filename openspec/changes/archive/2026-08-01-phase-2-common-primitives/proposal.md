## Why

Phase 2 establishes the shared domain primitives used by every bounded context. Without these building blocks—value objects, exceptions, events, specifications, clock, and ID generation—the Gmail, Intelligence, Search, and Notification contexts cannot be implemented.

## What Changes

- Introduce `ValueObject` base class and `UUIDId` value object in `Common/Domain/ValueObjects/`
- Introduce domain exception hierarchy (`DomainError`, `ValidationError`, `NotFoundError`, `PermissionError`, `ConcurrencyError`) in `Common/Domain/Exceptions/`
- Introduce `DomainEvent` base, `EventBus` protocol, and `InMemoryEventBus` in `Common/Domain/Events/`
- Introduce `Specification` pattern with composable `And`, `Or`, `Not` in `Common/Domain/Specifications/`
- Introduce `Clock` protocol with `SystemClock` and `TestClock` in `Common/Infrastructure/Clock/`
- Introduce `IdGenerator` protocol with `UuidIdGenerator` in `Common/Infrastructure/IdGenerator/`
- Unit tests for all primitives

## Capabilities

### New Capabilities
- `value-objects`: `ValueObject` base with equality/hashing/repr, and `UUIDId` wrapper
- `domain-exceptions`: Typed exception hierarchy for domain errors, validation, not-found, permissions, concurrency
- `domain-events`: `DomainEvent` base, `EventBus` protocol, and `InMemoryEventBus` implementation
- `specifications`: `Specification[T]` pattern with `And`, `Or`, `Not` composables
- `clock`: `Clock` protocol with `SystemClock` and injectable `TestClock`
- `id-generator`: `IdGenerator` protocol with `UuidIdGenerator`

### Modified Capabilities

## Impact

- New modules under `src/Common/Domain/` and `src/Common/Infrastructure/`
- All subsequent bounded contexts (Phases 3-7) depend on these primitives
- `tests/fakes/` and `tests/conftest.py` will use `TestClock` and `InMemoryEventBus` fixtures
- No external dependencies added
