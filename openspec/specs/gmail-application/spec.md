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

