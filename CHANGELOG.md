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
