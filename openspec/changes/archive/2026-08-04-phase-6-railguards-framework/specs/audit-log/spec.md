## ADDED Requirements

### Requirement: Audit log entry
The system SHALL provide an AuditLog entry capturing timestamp, action, email_id, details, and correlation_id for a write operation.

#### Scenario: Audit entry captures operation metadata
- **WHEN** an AuditLog entry is created for a write operation
- **THEN** it records the timestamp, action, email_id, details, and correlation_id

### Requirement: Audit log repository
The system SHALL provide an AuditLogRepository that persists audit entries, with a SQLite-backed implementation.

#### Scenario: Entry is persisted and retrievable
- **WHEN** an AuditLog entry is saved via the repository
- **THEN** it can be retrieved from the audit store

### Requirement: Audit log handler records write operations
The system SHALL provide an AuditLogHandler that subscribes to write domain events and persists an audit entry for each, preserving the correlation id.

#### Scenario: Forward event produces an audit entry
- **WHEN** an EmailForwarded event is published to the event bus
- **THEN** the handler persists an audit entry whose action reflects the forward and whose email_id matches the event

#### Scenario: Every write event is audited
- **WHEN** EmailArchived and EmailDeleted events are published
- **THEN** the handler persists a corresponding audit entry for each

#### Scenario: Correlation id is preserved
- **WHEN** a write operation carries a correlation id and its event is published
- **THEN** the persisted audit entry records that correlation id
