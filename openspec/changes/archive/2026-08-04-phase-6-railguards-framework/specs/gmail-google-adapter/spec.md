## ADDED Requirements

### Requirement: GmailApiGateway implements draft operations
The GmailApiGateway SHALL implement the GmailGateway draft operations against the Gmail `users.drafts` API, returning the gateway draft DTOs, with the same retry and rate-limiting applied to other calls.

#### Scenario: create_draft calls users.drafts.create
- **WHEN** GmailApiGateway.create_draft is called with a raw message
- **THEN** it invokes the drafts create endpoint and returns the draft id and message id from the response

#### Scenario: send_draft calls users.drafts.send
- **WHEN** GmailApiGateway.send_draft is called with a draft id
- **THEN** it invokes the drafts send endpoint and returns the sent message result

#### Scenario: delete_draft calls users.drafts.delete
- **WHEN** GmailApiGateway.delete_draft is called with a draft id
- **THEN** it invokes the drafts delete endpoint
