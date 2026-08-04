# gmail-domain Specification

## Purpose
TBD - normalized during phase-6 archive. Update Purpose after archive.
## Requirements
### Requirement: EmailAddress value object validation
The system SHALL validate email addresses against RFC 5322 format (local-part@domain) with a maximum length of 254 characters.

#### Scenario: Valid email address creation
- **WHEN** an EmailAddress is created with "user@example.com"
- **THEN** the value object is created successfully with local_part="user" and domain="example.com"

#### Scenario: Invalid email format rejected
- **WHEN** an EmailAddress is created with "invalid-email"
- **THEN** a ValidationError is raised

#### Scenario: Email address exceeds maximum length
- **WHEN** an EmailAddress is created with a string exceeding 254 characters
- **THEN** a ValidationError is raised

#### Scenario: Plus addressing supported
- **WHEN** an EmailAddress is created with "user+tag@example.com"
- **THEN** the value object is created successfully with local_part="user+tag"

#### Scenario: Subdomain email supported
- **WHEN** an EmailAddress is created with "user@mail.subdomain.example.com"
- **THEN** the value object is created successfully

### Requirement: Gmail-specific value objects
The system SHALL provide immutable value objects for Gmail identifiers: GmailMessageId, ThreadId, HistoryId, and GmailQuery.

#### Scenario: GmailMessageId wraps string identifier
- **WHEN** a GmailMessageId is created with a non-empty string
- **THEN** the value object stores the identifier immutably

#### Scenario: ThreadId wraps string identifier
- **WHEN** a ThreadId is created with a non-empty string
- **THEN** the value object stores the identifier immutably

#### Scenario: HistoryId wraps monotonically increasing string
- **WHEN** a HistoryId is created with a non-empty string
- **THEN** the value object stores the identifier immutably

#### Scenario: GmailQuery validates non-empty and max length
- **WHEN** a GmailQuery is created with an empty string
- **THEN** a ValidationError is raised

#### Scenario: GmailQuery builders compose correctly
- **WHEN** a GmailQuery is built using from_sender("alice@example.com") and with_subject("invoice")
- **THEN** the query string contains both criteria

#### Scenario: GmailQuery date_range builder
- **WHEN** a GmailQuery is built using date_range with start and end dates
- **THEN** the query string contains the after:/before: filters

#### Scenario: GmailQuery has_attachment builder
- **WHEN** a GmailQuery is built using has_attachment()
- **THEN** the query string contains "has:attachment"

#### Scenario: GmailQuery unread builder
- **WHEN** a GmailQuery is built using unread()
- **THEN** the query string contains "is:unread"

### Requirement: Email aggregate root
The system SHALL model Email as an aggregate root with behaviors for mark_read, add_label, remove_label, archive, move_to_trash, and restore_from_trash.

#### Scenario: Email created from Gmail API response
- **WHEN** Email.from_gmail_message() is called with mapped Gmail data
- **THEN** an Email aggregate is created with all required fields populated

#### Scenario: Email marked as read
- **WHEN** mark_read() is called on an unread Email
- **THEN** is_read is set to True and a domain event is appended

#### Scenario: Label added to email
- **WHEN** add_label("Important") is called
- **THEN** the label is added to the labels set and an EmailLabeled event is appended

#### Scenario: Duplicate label prevented
- **WHEN** add_label("Important") is called and "Important" is already in labels
- **THEN** the labels set remains unchanged (unique constraint)

#### Scenario: Email archived
- **WHEN** archive() is called
- **THEN** an EmailArchived domain event is appended

#### Scenario: Email moved to trash
- **WHEN** move_to_trash() is called
- **THEN** the email is marked as trashed and an EmailDeleted event is appended

#### Scenario: Email restored from trash
- **WHEN** restore_from_trash() is called on a trashed email
- **THEN** the email is un-trashed

#### Scenario: Restore fails for non-trashed email
- **WHEN** restore_from_trash() is called on a non-trashed email
- **THEN** a DomainError is raised

### Requirement: Thread aggregate root
The system SHALL model Thread as an aggregate root containing an ordered list of email IDs with behaviors for adding emails, marking read, labeling, archiving, and trashing.

#### Scenario: Thread created with emails
- **WHEN** a Thread is created with email IDs
- **THEN** the emails are stored in date order

#### Scenario: Email added to thread
- **WHEN** add_email(email_id) is called
- **THEN** the email ID is appended to the ordered list

#### Scenario: Thread marked as read
- **WHEN** mark_read() is called on a Thread
- **THEN** is_read is set to True

#### Scenario: Thread cannot be empty
- **WHEN** a Thread is created without any email IDs
- **THEN** a ValidationError is raised

### Requirement: Attachment entity
The system SHALL model Attachment as an entity with file metadata and Gmail attachment ID.

#### Scenario: Attachment created with metadata
- **WHEN** an Attachment is created with file_name, mime_type, size_bytes, and attachment_id
- **THEN** the entity is created with all fields validated

#### Scenario: AttachmentMetadata value object validation
- **WHEN** AttachmentMetadata is created with negative size_bytes
- **THEN** a ValidationError is raised

### Requirement: Label entity with system label protection
The system SHALL model Label as an entity that prevents renaming or deletion of system labels.

#### Scenario: User label renamed
- **WHEN** rename("New Name") is called on a user-created Label
- **THEN** the label name is updated

#### Scenario: System label rename blocked
- **WHEN** rename("Custom") is called on a system Label (type="system")
- **THEN** a DomainError is raised

#### Scenario: System label identification
- **WHEN** a Label is created with type="system"
- **THEN** the label is marked as non-modifiable

### Requirement: Repository ports
The system SHALL define EmailRepository and ThreadRepository protocols with find, search, save, and delete operations.

#### Scenario: Email found by UUID
- **WHEN** find_by_id(uuid) is called on EmailRepository
- **THEN** the matching Email is returned or None

#### Scenario: Email found by Gmail message ID
- **WHEN** find_by_gmail_message_id(message_id) is called
- **THEN** the matching Email is returned or None

#### Scenario: Emails searched by query
- **WHEN** search(gmail_query) is called
- **THEN** a list of matching EmailDTOs is returned

#### Scenario: Unread emails listed
- **WHEN** list_unread(limit) is called
- **THEN** up to limit unread emails are returned

#### Scenario: Thread found by Gmail thread ID
- **WHEN** find_by_gmail_thread_id(thread_id) is called on ThreadRepository
- **THEN** the matching Thread is returned or None

### Requirement: GmailGateway anti-corruption layer
The system SHALL define GmailGateway port with methods for all Gmail API operations.

#### Scenario: Messages listed with pagination
- **WHEN** list_messages(query, page_token, max_results) is called
- **THEN** a GmailListResponse with messages and next page token is returned

#### Scenario: Message retrieved by ID
- **WHEN** get_message(message_id, format) is called
- **THEN** a GmailMessage with the requested format is returned

#### Scenario: Message sent
- **WHEN** send_message(raw_message) is called
- **THEN** a SentMessageResult with message_id and thread_id is returned

#### Scenario: Message labels modified
- **WHEN** modify_message(message_id, add_labels, remove_labels) is called
- **THEN** a ModifyResult is returned

#### Scenario: Attachment downloaded
- **WHEN** download_attachment(message_id, attachment_id) is called
- **THEN** the attachment bytes are returned

#### Scenario: Gmail watch established
- **WHEN** watch(notification_url, webhook_token) is called
- **THEN** a WatchResponse with expiration is returned

### Requirement: Domain mappers
The system SHALL provide mappers to convert Gmail API responses to domain entities.

#### Scenario: Email mapped from gateway response
- **WHEN** EmailMapper.to_domain(gateway_message) is called
- **THEN** an Email aggregate is returned with correctly mapped fields

#### Scenario: Thread mapped from gateway response
- **WHEN** ThreadMapper.to_domain(gateway_thread) is called
- **THEN** a Thread aggregate is returned with correctly mapped fields

### Requirement: Gmail domain events
The system SHALL define domain events for Gmail operations: EmailReceived, EmailArchived, EmailDeleted, EmailForwarded, EmailLabeled, InboxSynchronized.

#### Scenario: EmailReceived event created
- **WHEN** an EmailReceived event is instantiated
- **THEN** it contains email_id, from_address, subject, and received_at

#### Scenario: EmailLabeled event created
- **WHEN** an EmailLabeled event is instantiated
- **THEN** it contains email_id, label_name, and labeled_at

#### Scenario: InboxSynchronized event created
- **WHEN** an InboxSynchronized event is instantiated
- **THEN** it contains history_id, synchronized_at, and email_count

### Requirement: GmailGateway draft operations
The GmailGateway port SHALL provide draft operations — `create_draft`, `send_draft`, and `delete_draft` — with their gateway DTOs, so drafts can be created for human review, sent, or discarded without composing and sending in one step.

#### Scenario: create_draft returns a draft identifier
- **WHEN** create_draft is called with a raw message
- **THEN** it returns a draft result containing the draft id and the associated message id

#### Scenario: send_draft sends an existing draft
- **WHEN** send_draft is called with a draft id
- **THEN** it sends the draft and returns the sent message result

#### Scenario: delete_draft discards a draft
- **WHEN** delete_draft is called with a draft id
- **THEN** the draft is removed

