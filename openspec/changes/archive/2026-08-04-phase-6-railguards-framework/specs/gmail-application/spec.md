## ADDED Requirements

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
