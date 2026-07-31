## ADDED Requirements

### Requirement: IdGenerator protocol defines generate()
`IdGenerator` SHALL define a `generate() -> UUIDId` method.

#### Scenario: Generate returns UUIDId
- **WHEN** `IdGenerator.generate()` is called
- **THEN** it returns a `UUIDId` instance

### Requirement: UuidIdGenerator produces unique IDs
`UuidIdGenerator.generate()` SHALL return a unique `UUIDId` on each call.

#### Scenario: Uniqueness
- **WHEN** `generate()` is called twice
- **THEN** the returned `UUIDId` instances are not equal

#### Scenario: Type correctness
- **WHEN** `generate()` is called
- **THEN** the return value is an instance of `UUIDId`
