# value-objects Specification

## Purpose
Defines the shared value-object base (value semantics) and the UUIDId identifier value object.

## Requirements

### Requirement: ValueObject base provides value semantics
The `ValueObject` base class SHALL provide structural equality, hashing, and string representation based on all attributes.

#### Scenario: Equal values
- **WHEN** two value objects have identical attribute values
- **THEN** they compare equal via `__eq__`

#### Scenario: Different values
- **WHEN** two value objects differ in any attribute
- **THEN** they compare not equal

#### Scenario: Hash consistency
- **WHEN** two value objects are equal
- **THEN** their `__hash__` values are identical

#### Scenario: Repr output
- **WHEN** `repr()` is called on a value object
- **THEN** the output includes the class name and all attribute values

### Requirement: UUIDId wraps uuid.UUID
`UUIDId` SHALL wrap a `uuid.UUID` instance and provide a `generate()` factory.

#### Scenario: UUID generation
- **WHEN** `UUIDId.generate()` is called
- **THEN** a new `UUIDId` wrapping a random `uuid.UUID` is returned

#### Scenario: UUID uniqueness
- **WHEN** two `UUIDId` instances are generated
- **THEN** they are not equal

#### Scenario: UUID equality
- **WHEN** two `UUIDId` instances wrap the same UUID
- **THEN** they compare equal and have the same hash
