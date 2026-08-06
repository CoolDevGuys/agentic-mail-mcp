# specifications Specification

## Purpose
Defines the Specification pattern (composable is_satisfied_by predicates with And/Or/Not) for expressing domain rules.

## Requirements

### Requirement: Specification base defines is_satisfied_by
`Specification[T]` SHALL define an abstract `is_satisfied_by(candidate: T) -> bool` method.

#### Scenario: Satisfaction check
- **WHEN** `is_satisfied_by` is called with a candidate
- **THEN** it returns `True` if the candidate satisfies the specification

#### Scenario: Non-satisfaction
- **WHEN** `is_satisfied_by` is called with a non-matching candidate
- **THEN** it returns `False`

### Requirement: AndSpecification composes two specifications with AND
`AndSpecification` SHALL return `True` only when both component specifications are satisfied.

#### Scenario: Both satisfied
- **WHEN** both component specifications are satisfied by the candidate
- **THEN** `AndSpecification.is_satisfied_by` returns `True`

#### Scenario: One not satisfied
- **WHEN** either component specification is not satisfied
- **THEN** `AndSpecification.is_satisfied_by` returns `False`

### Requirement: OrSpecification composes two specifications with OR
`OrSpecification` SHALL return `True` when at least one component specification is satisfied.

#### Scenario: One satisfied
- **WHEN** at least one component specification is satisfied
- **THEN** `OrSpecification.is_satisfied_by` returns `True`

#### Scenario: None satisfied
- **WHEN** neither component specification is satisfied
- **THEN** `OrSpecification.is_satisfied_by` returns `False`

### Requirement: NotSpecification negates a specification
`NotSpecification` SHALL return the inverse of the wrapped specification.

#### Scenario: Negation
- **WHEN** the wrapped specification is satisfied
- **THEN** `NotSpecification.is_satisfied_by` returns `False`

#### Scenario: Double negation
- **WHEN** the wrapped specification is not satisfied
- **THEN** `NotSpecification.is_satisfied_by` returns `True`

### Requirement: Specifications are chainable
Specification composables SHALL be composable with other composables to arbitrary depth.

#### Scenario: Chained composition
- **WHEN** `AndSpecification(OrSpec(a, b), NotSpec(c))` is evaluated
- **THEN** the result follows boolean logic: `(a OR b) AND (NOT c)`
