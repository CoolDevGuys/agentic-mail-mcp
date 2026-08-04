## ADDED Requirements

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
