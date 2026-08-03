# gmail-persistence Specification

## Purpose
TBD - created by archiving change phase-5-infrastructure-adapters. Update Purpose after archive.
## Requirements
### Requirement: SQLAlchemy models and domain mappers
The system SHALL define SQLAlchemy ORM models for Email, Thread, Attachment, and Label, with mappers translating between domain entities and ORM rows in both directions.

#### Scenario: Domain entity maps to an ORM row and back
- **WHEN** an Email domain entity is mapped to its ORM model and back to a domain entity
- **THEN** the round-tripped entity preserves its identifiers, fields, labels, and read state

### Requirement: SQLite repository implementations
The system SHALL provide SqliteEmailRepository and SqliteThreadRepository that implement the EmailRepository and ThreadRepository ports against a synchronous SQLite database.

#### Scenario: Save then find an email by id
- **WHEN** an email is saved and then fetched by its UUID
- **THEN** the repository returns the persisted email

#### Scenario: Find by Gmail message id
- **WHEN** an email is saved and fetched by its Gmail message id
- **THEN** the repository returns the matching email

#### Scenario: List unread respects the limit
- **WHEN** more unread emails exist than the requested limit
- **THEN** the repository returns at most the limit

#### Scenario: Missing email returns None
- **WHEN** an email id that was never saved is requested
- **THEN** the repository returns None

#### Scenario: Save then find a thread by Gmail thread id
- **WHEN** a thread is saved and fetched by its Gmail thread id
- **THEN** the repository returns the persisted thread with its ordered email ids

### Requirement: Alembic migration creates the initial schema
The system SHALL provide an Alembic configuration (alembic.ini at the repo root, a single migrations directory) whose initial migration creates the Email, Thread, Attachment, and Label tables.

#### Scenario: Upgrade builds the schema
- **WHEN** the initial migration is applied to an empty database
- **THEN** the Email, Thread, Attachment, and Label tables exist

### Requirement: Optional PostgreSQL repositories
The system SHALL provide PostgreSQL repository implementations that satisfy the same repository ports and share the same schema, available only when the PostgreSQL extra is installed.

#### Scenario: PostgreSQL repository satisfies the repository contract
- **WHEN** the shared repository contract test runs against the PostgreSQL implementation
- **THEN** it passes the same assertions as the SQLite implementation

