## 1. Value Objects

- [x] 1.1 Implement `ValueObject` base class in `src/Common/Domain/ValueObjects/base.py` with structural `__eq__`, `__hash__`, `__repr__`
- [x] 1.2 Implement `UUIDId` in `src/Common/Domain/ValueObjects/uuid_id.py` wrapping `uuid.UUID` with `generate()` factory
- [x] 1.3 Write unit tests for `ValueObject` equality, hashing, repr, and `UUIDId` generation/uniqueness

## 2. Domain Exceptions

- [x] 2.1 Implement `DomainError` base in `src/Common/Domain/Exceptions/__init__.py` with `message` and `context` dict
- [x] 2.2 Implement `ValidationError`, `NotFoundError`, `PermissionError`, `ConcurrencyError` inheriting from `DomainError`
- [x] 2.3 Write unit tests for exception instantiation, message propagation, and context

## 3. Domain Events

- [x] 3.1 Implement `DomainEvent` base in `src/Common/Domain/Events/__init__.py` with `event_id`, `occurred_at`, `aggregate_id`
- [x] 3.2 Define `EventBus` protocol with `publish`, `subscribe`, `publish_all`
- [x] 3.3 Implement `InMemoryEventBus` with synchronous in-memory dispatch
- [x] 3.4 Write unit tests for publish/subscribe flow, multiple handlers, event ordering, and `publish_all`

## 4. Specifications

- [x] 4.1 Implement `Specification[T]` base in `src/Common/Domain/Specifications/__init__.py` with abstract `is_satisfied_by`
- [x] 4.2 Implement `AndSpecification`, `OrSpecification`, `NotSpecification` composables
- [x] 4.3 Write unit tests for composition logic, chained specifications, and edge cases

## 5. Clock

- [x] 5.1 Implement `Clock` protocol in `src/Common/Infrastructure/Clock/__init__.py` with `now() -> datetime`
- [x] 5.2 Implement `SystemClock` wrapping `datetime.now(timezone.utc)`
- [x] 5.3 Implement `FrozenClock` with injectable `set(datetime)` method
- [x] 5.4 Write unit tests for UTC correctness and test clock time injection

## 6. ID Generator

- [x] 6.1 Implement `IdGenerator` protocol in `src/Common/Infrastructure/IdGenerator/__init__.py` with `generate() -> UUIDId`
- [x] 6.2 Implement `UuidIdGenerator` wrapping `uuid.uuid4()`
- [x] 6.3 Write unit tests for uniqueness and type correctness
