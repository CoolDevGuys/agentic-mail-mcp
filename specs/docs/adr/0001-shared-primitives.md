# 0001 — Shared Domain Primitives via Protocols

Status: accepted

Context: Phase 2 introduces shared primitives used by every bounded context: value objects, domain events, exceptions, specifications, clock, and ID generation. Each primitive needs to be testable, framework-agnostic, and swappable without affecting dependent code.

Decision: Shared primitives are implemented as `typing.Protocol` abstractions with default implementations in `agentic_mail_mcp/Common/`. Key choices:

- **ValueObject** inherits from `dataclasses.dataclass(frozen=True)` to enforce immutability and provide structural equality, hashing, and repr out of the box.
- **UUIDId** wraps `uuid.UUID` (not `str`) to leverage built-in validation and formatting, with a `generate()` factory method.
- **Exception hierarchy** is flat under `DomainError`, which carries a `context: dict` for structured error details. Subclasses: `ValidationError`, `NotFoundError`, `PermissionError`, `ConcurrencyError`.
- **EventBus** is a Protocol with `publish`, `subscribe`, and `publish_all`. `InMemoryEventBus` provides a synchronous implementation for tests and lightweight deployments.
- **Specification[T]** is a generic abstract class with compositional `and_`, `or_`, `not_` operators. Concrete compositions: `AndSpecification`, `OrSpecification`, `NotSpecification`.
- **Clock** is a Protocol with `now() -> datetime`. `SystemClock` delegates to `datetime.now(UTC)`. `FrozenClock` allows deterministic time in tests.
- **IdGenerator** is a Protocol with `generate() -> UUIDId`. `UuidIdGenerator` wraps `uuid.uuid4()`.

Consequences:

- **Easier:** All time-dependent and ID-dependent code is testable via injectable abstractions. Bounded contexts depend on protocols, not implementations. External event bus adapters (Phase 5) satisfy the same protocol without inheritance.
- **Harder:** Protocol-based dependencies require explicit wiring in the DI container. Runtime type checking is not enforced for generic `Specification[T]`; mypy is the enforcement point.
- **Future:** Alternative ID schemes (ULID, snowflake) or async event buses require only new implementations of the existing protocols, no changes to call sites.
