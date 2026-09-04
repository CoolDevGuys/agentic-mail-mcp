## MODIFIED Requirements

### Requirement: Read DTOs
The system SHALL provide plain-data DTOs distinct from domain entities: EmailDTO, ThreadDTO, and LabelDTO, produced by the read use cases. EmailDTO SHALL expose the sender display name separately from the bare sender address on live gateway paths, and SHALL produce snippets free of invisible Unicode characters with consistent truncation.

#### Scenario: EmailDTO maps from an Email aggregate
- **WHEN** an EmailDTO is produced from an Email domain entity
- **THEN** the DTO carries the email's identifiers, subject, snippet, addresses, date, read state, and labels without any domain behavior

#### Scenario: Gateway sender splits into address and display name
- **WHEN** an EmailDTO is produced from a gateway message whose raw From header is `"Will G. <inmail-hit-reply@linkedin.com>"`
- **THEN** `from_address` is `inmail-hit-reply@linkedin.com`
- **AND** `from_display_name` is `Will G.`

#### Scenario: Bare sender header yields no display name
- **WHEN** an EmailDTO is produced from a gateway message whose From header is a bare address
- **THEN** `from_address` is that address and `from_display_name` is null

#### Scenario: Snippets are stripped of invisible characters and truncated consistently
- **WHEN** a snippet is derived from a body (or from the gateway fallback snippet) that contains zero-width or other invisible Unicode characters
- **THEN** those characters are removed, whitespace is collapsed, and text exceeding the snippet limit is truncated with an ellipsis

### Requirement: SearchEmailsUseCase
The system SHALL provide SearchEmailsUseCase that builds a GmailQuery from a SearchEmailsQuery and returns a paginated SearchEmailsResult of EmailDTOs, resolving results via either the live GmailGateway or the local EmailRepository as configured. A SearchEmailsQuery SHALL carry a `query_scope` (`all`, `subject`, or `body`) that restricts where the free-text term is matched.

#### Scenario: Search returns paginated results from the gateway
- **WHEN** SearchEmailsUseCase.execute is called with a SearchEmailsQuery and the gateway returns matching messages
- **THEN** the use case returns a SearchEmailsResult containing EmailDTOs and pagination metadata

#### Scenario: Query scope compiles to a field-restricted Gmail query
- **WHEN** a SearchEmailsQuery with scope `subject` and a query term is built into a GmailQuery
- **THEN** the term is applied via the Gmail `subject:` operator (and via `inbody:` for scope `body`)
- **AND** scope `all` keeps the term unrestricted as before

#### Scenario: Invalid query scope is rejected
- **WHEN** a SearchEmailsQuery is constructed with a query_scope outside `all`, `subject`, `body`
- **THEN** a ValidationError is raised

#### Scenario: Search returns empty result set
- **WHEN** SearchEmailsUseCase.execute is called and no messages match the query
- **THEN** the use case returns a SearchEmailsResult with an empty list and no error

#### Scenario: Search resolves from the local repository when configured for cache
- **WHEN** SearchEmailsUseCase is configured to use the EmailRepository and execute is called
- **THEN** results are resolved via EmailRepository.search() rather than the gateway
