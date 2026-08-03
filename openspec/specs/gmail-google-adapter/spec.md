# gmail-google-adapter Specification

## Purpose
TBD - created by archiving change phase-5-infrastructure-adapters. Update Purpose after archive.
## Requirements
### Requirement: OAuth2 provider with encrypted token storage
The system SHALL provide a GmailOAuthProvider that authenticates via OAuth2 (interactive browser flow and headless pre-authorized tokens), persists refresh tokens to the configured storage path outside the repository, and encrypts them at rest using the configured encryption key. Token values SHALL never be written to logs.

#### Scenario: Interactive authorization stores an encrypted token
- **WHEN** the interactive OAuth2 flow completes successfully
- **THEN** the refresh token is written to Settings.gmail.token_storage_path encrypted with Settings.gmail.token_encryption_key

#### Scenario: Headless flow uses a pre-authorized token
- **WHEN** a valid pre-authorized token exists at the storage path
- **THEN** the provider loads and decrypts it without launching an interactive flow

#### Scenario: Missing or invalid encryption key fails fast
- **WHEN** a stored token cannot be decrypted with the configured key
- **THEN** the provider raises a domain error and does not log the token value

### Requirement: GmailApiGateway implements the GmailGateway port
The system SHALL provide a GmailApiGateway that implements every GmailGateway method using the Google API client, returning the gateway DTOs defined by the port, with retry and rate limiting around API calls.

#### Scenario: list_messages returns a GmailListResponse
- **WHEN** GmailApiGateway.list_messages is called with a query
- **THEN** it returns a GmailListResponse containing message headers and a next page token

#### Scenario: get_message returns None when the message does not exist
- **WHEN** GmailApiGateway.get_message is called with an unknown message id
- **THEN** it returns None rather than raising

#### Scenario: Transient API errors are retried
- **WHEN** the Gmail API returns a 429 or 5xx response
- **THEN** the gateway retries with backoff before surfacing an error

#### Scenario: Rate limit caps request throughput
- **WHEN** calls exceed the configured rate limit
- **THEN** the gateway throttles requests rather than exceeding the limit

### Requirement: Gmail push-notification watcher
The system SHALL provide a GmailWatcher that starts and stops Gmail push notifications and processes webhook callbacks.

#### Scenario: Start watch returns an expiration
- **WHEN** GmailWatcher starts a watch for a notification URL
- **THEN** it returns a WatchResponse containing the watch expiration

#### Scenario: Stop watch succeeds
- **WHEN** GmailWatcher stops the active watch
- **THEN** it returns a successful StopWatchResult

### Requirement: History synchronizer applies deltas and emits events
The system SHALL provide a GmailHistorySynchronizer that processes Gmail history changes, updates the local cache, and publishes the corresponding domain events.

#### Scenario: New messages emit EmailReceived and update the cache
- **WHEN** the synchronizer processes a history delta containing new messages
- **THEN** the messages are persisted to the local repository and an InboxSynchronized event (and per-message events) are published

#### Scenario: Synchronization is idempotent for an already-applied history id
- **WHEN** the synchronizer is run twice for the same start history id
- **THEN** the second run applies no duplicate changes

