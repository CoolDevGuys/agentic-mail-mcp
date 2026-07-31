## ADDED Requirements

### Requirement: Clock protocol defines now()
`Clock` SHALL define a `now() -> datetime` method.

#### Scenario: Clock interface
- **WHEN** `Clock.now()` is called
- **THEN** it returns a `datetime` object

### Requirement: SystemClock returns current UTC time
`SystemClock.now()` SHALL return the current UTC-aware datetime.

#### Scenario: UTC time
- **WHEN** `SystemClock.now()` is called
- **THEN** the returned datetime has `tzinfo` set to UTC

### Requirement: TestClock returns injectable time
`TestClock` SHALL allow setting a fixed datetime that `now()` returns.

#### Scenario: Fixed time
- **WHEN** `TestClock.set(datetime(2025, 1, 1))` is called
- **THEN** subsequent `now()` calls return `datetime(2025, 1, 1)`

#### Scenario: Time advancement
- **WHEN** `TestClock.set()` is called with a new datetime
- **THEN** subsequent `now()` calls return the new datetime
