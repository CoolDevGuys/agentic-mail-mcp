# gmail-application Specification

## Purpose
TBD - created by archiving change phase-4-application-use-cases. Update Purpose after archive.
## Requirements
### Requirement: Read query objects
The system SHALL provide validated query objects for read operations: SearchEmailsQuery, GetEmailQuery, GetThreadQuery, ListUnreadQuery, and ListLabelsQuery.

#### Scenario: SearchEmailsQuery accepts search criteria
- **WHEN** a SearchEmailsQuery is created with query_string, from_address, subject, date_from, date_to, has_attachment, label, unread_only, page, and page_size
- **THEN** the query object stores all criteria and exposes them for use-case consumption

#### Scenario: SearchEmailsQuery rejects invalid pagination
- **WHEN** a SearchEmailsQuery is created with page_size less than 1 or page less than 1
- **THEN** a ValidationError is raised

#### Scenario: GetEmailQuery accepts a UUID or Gmail message id
- **WHEN** a GetEmailQuery is created with an email_id that is either a UUID or a GmailMessageId
- **THEN** the query object stores the identifier and records which identifier kind was provided

#### Scenario: ListLabelsQuery validates label type
- **WHEN** a ListLabelsQuery is created with a label_type outside {system, user, all}
- **THEN** a ValidationError is raised

### Requirement: Command objects
The system SHALL provide validated command objects for write operations: ForwardEmailCommand, ArchiveEmailCommand, DeleteEmailCommand, CreateDraftCommand, SendDraftCommand, AddLabelCommand, and MarkReadCommand. Command execution handlers for the write path are out of scope for this capability and are delivered with the railguards framework.

#### Scenario: ForwardEmailCommand requires a recipient
- **WHEN** a ForwardEmailCommand is created without a to_address
- **THEN** a ValidationError is raised

#### Scenario: DeleteEmailCommand defaults to non-permanent
- **WHEN** a DeleteEmailCommand is created without specifying permanent
- **THEN** the command's permanent flag defaults to False

#### Scenario: AddLabelCommand requires email_id and label_name
- **WHEN** an AddLabelCommand is created with a missing email_id or empty label_name
- **THEN** a ValidationError is raised

### Requirement: Read DTOs
The system SHALL provide plain-data DTOs distinct from domain entities: EmailDTO, ThreadDTO, and LabelDTO, produced by the read use cases.

#### Scenario: EmailDTO maps from an Email aggregate
- **WHEN** an EmailDTO is produced from an Email domain entity
- **THEN** the DTO carries the email's identifiers, subject, snippet, addresses, date, read state, and labels without any domain behavior

### Requirement: SearchEmailsUseCase
The system SHALL provide SearchEmailsUseCase that builds a GmailQuery from a SearchEmailsQuery and returns a paginated SearchEmailsResult of EmailDTOs, resolving results via either the live GmailGateway or the local EmailRepository as configured.

#### Scenario: Search returns paginated results from the gateway
- **WHEN** SearchEmailsUseCase.execute is called with a SearchEmailsQuery and the gateway returns matching messages
- **THEN** the use case returns a SearchEmailsResult containing EmailDTOs and pagination metadata

#### Scenario: Search returns empty result set
- **WHEN** SearchEmailsUseCase.execute is called and no messages match the query
- **THEN** the use case returns a SearchEmailsResult with an empty list and no error

#### Scenario: Search resolves from the local repository when configured for cache
- **WHEN** SearchEmailsUseCase is configured to use the EmailRepository and execute is called
- **THEN** results are resolved via EmailRepository.search() rather than the gateway

### Requirement: GetEmailUseCase
The system SHALL provide GetEmailUseCase that resolves an email by UUID from the local repository or by GmailMessageId via the gateway, returning an EmailDTO including the body, and falling back to the gateway on a local cache miss.

#### Scenario: Resolve by UUID from local cache
- **WHEN** GetEmailUseCase.execute is called with a GetEmailQuery holding a UUID present in the repository
- **THEN** the use case returns the EmailDTO from the local repository

#### Scenario: Cache miss falls back to gateway
- **WHEN** GetEmailUseCase.execute is called with an id not present locally
- **THEN** the use case fetches the message via the GmailGateway and returns the EmailDTO

#### Scenario: Email not found
- **WHEN** GetEmailUseCase.execute is called with an id not present locally or via the gateway
- **THEN** a NotFoundError is raised

### Requirement: GetThreadUseCase
The system SHALL provide GetThreadUseCase that resolves a thread and its ordered email IDs and returns a ThreadDTO.

#### Scenario: Resolve thread with its emails
- **WHEN** GetThreadUseCase.execute is called with a GetThreadQuery for an existing thread
- **THEN** the use case returns a ThreadDTO containing the thread metadata and its ordered email IDs

#### Scenario: Thread not found
- **WHEN** GetThreadUseCase.execute is called for a thread that does not exist
- **THEN** a NotFoundError is raised

### Requirement: ListUnreadUseCase
The system SHALL provide ListUnreadUseCase that returns a paginated list of unread EmailDTOs, optionally filtered by label.

#### Scenario: List unread without label filter
- **WHEN** ListUnreadUseCase.execute is called with a ListUnreadQuery and no label
- **THEN** the use case returns unread EmailDTOs limited by the query's limit

#### Scenario: List unread filtered by label
- **WHEN** ListUnreadUseCase.execute is called with a ListUnreadQuery specifying a label
- **THEN** only unread emails carrying that label are returned

### Requirement: ListLabelsUseCase
The system SHALL provide ListLabelsUseCase that returns LabelDTOs filtered by type (system, user, or all).

#### Scenario: List all labels
- **WHEN** ListLabelsUseCase.execute is called with label_type "all"
- **THEN** the use case returns LabelDTOs for both system and user labels

#### Scenario: List only user labels
- **WHEN** ListLabelsUseCase.execute is called with label_type "user"
- **THEN** the use case returns LabelDTOs for user labels only

### Requirement: ForwardEmailUseCase
The system SHALL provide ForwardEmailUseCase that validates a ForwardEmailCommand against the railguards, builds a forwarded message with the original as an RFC822 attachment, sends it via the GmailGateway, and publishes an EmailForwarded event.

#### Scenario: Allowed recipient forwards and emits event
- **WHEN** ForwardEmailUseCase.execute runs with an allowed recipient under read-write access
- **THEN** the message is sent via the gateway and an EmailForwarded event is published to the event bus with the email id and recipient

#### Scenario: Blocked recipient is denied
- **WHEN** ForwardEmailUseCase.execute runs with a recipient not on the allowlist
- **THEN** a PermissionError is raised and no message is sent

#### Scenario: Rate limit exceeded is denied
- **WHEN** the forward rate limit for the window has been reached
- **THEN** ForwardEmailUseCase.execute raises a PermissionError and no message is sent

### Requirement: ArchiveEmailUseCase
The system SHALL provide ArchiveEmailUseCase that validates an ArchiveEmailCommand against the railguards, removes the INBOX label via the GmailGateway, and publishes an EmailArchived event.

#### Scenario: Archive removes INBOX and emits event
- **WHEN** ArchiveEmailUseCase.execute runs for an allowed email
- **THEN** the INBOX label is removed via modify_message and an EmailArchived event is published with the email id

#### Scenario: Blocked action is denied
- **WHEN** the archive action is blocked by the railguards
- **THEN** a PermissionError is raised and no modification is made

### Requirement: DeleteEmailUseCase
The system SHALL provide DeleteEmailUseCase that soft-deletes (trash) by default and permanently deletes only when the command requests it, the action is not blocked, and the archive-first policy is satisfied; it publishes an EmailDeleted event.

#### Scenario: Soft delete trashes the email
- **WHEN** DeleteEmailUseCase.execute runs with permanent=False
- **THEN** the email is trashed via the gateway and an EmailDeleted event is published

#### Scenario: Permanent delete blocked by policy
- **WHEN** DeleteEmailUseCase.execute runs with permanent=True but permanent delete is blocked or archive-first is unsatisfied
- **THEN** a PermissionError is raised and the email is not permanently deleted

#### Scenario: Permanent delete permitted when archived and allowed
- **WHEN** DeleteEmailUseCase.execute runs with permanent=True, the action is allowed, and the email is archived
- **THEN** the email is permanently deleted via the gateway and an EmailDeleted event is published

### Requirement: Draft-first sending use cases
The system SHALL provide CreateDraftUseCase that creates a draft via the GmailGateway without sending and returns the draft id, and SendDraftUseCase that sends a previously created draft.

#### Scenario: Create draft returns a draft id without sending
- **WHEN** CreateDraftUseCase.execute runs with a CreateDraftCommand under read-write access
- **THEN** a draft is created via the gateway, no message is sent, and the draft id is returned

#### Scenario: Send draft sends the reviewed draft
- **WHEN** SendDraftUseCase.execute runs with a SendDraftCommand referencing an existing draft
- **THEN** the draft is sent via the gateway

#### Scenario: Draft creation denied under read-only
- **WHEN** CreateDraftUseCase.execute runs while access_level is read_only
- **THEN** a PermissionError is raised and no draft is created

