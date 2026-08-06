# domain-exceptions Specification

## Purpose
Defines the typed domain exception hierarchy that expresses failure conditions independently of transport or framework.

## Requirements

### Requirement: DomainError is the base exception
`DomainError` SHALL be the base exception for all domain-layer errors and SHALL carry a `message` and optional `context` dict.

#### Scenario: Basic instantiation
- **WHEN** `DomainError("something failed")` is raised
- **THEN** the exception message contains "something failed"

#### Scenario: Context propagation
- **WHEN** `DomainError("failed", context={"key": "value"})` is raised
- **THEN** the `context` attribute contains `{"key": "value"}`

### Requirement: ValidationError signals validation failures
`ValidationError` SHALL indicate value object or entity validation failures.

#### Scenario: Validation error
- **WHEN** a value object fails validation
- **THEN** `ValidationError` is raised with a descriptive message

### Requirement: NotFoundError signals missing entities
`NotFoundError` SHALL indicate an entity was not found by its ID.

#### Scenario: Entity not found
- **WHEN** a repository lookup returns nothing
- **THEN** `NotFoundError` is raised with the entity ID in context

### Requirement: PermissionError signals authorization failures
`PermissionError` SHALL indicate railguard or authorization violations.

#### Scenario: Permission denied
- **WHEN** a railguard check fails
- **THEN** `PermissionError` is raised with the denied action in context

### Requirement: ConcurrencyError signals optimistic lock failures
`ConcurrencyError` SHALL indicate concurrent modification conflicts.

#### Scenario: Concurrent modification
- **WHEN** an entity is modified by two concurrent operations
- **THEN** `ConcurrencyError` is raised on the losing operation
