## ADDED Requirements

### Requirement: Structured tool results
Every MCP tool SHALL produce real structured content in its `CallToolResult`
(unwrapped), so agents can consume the payload as an object without parsing a
JSON string returned as text.

#### Scenario: Tool results carry structured content
- **WHEN** a registered tool handler returns its result dictionary
- **THEN** the MCP SDK derives an output schema for it (the handler's return
  annotation is `dict[str, Any]`, not a bare `dict`)
- **AND** the call result carries the result as a structured object rather than
  only as a JSON-encoded text payload

## MODIFIED Requirements

### Requirement: Read tools
The system SHALL provide read tools that each wrap a single read use case: `SearchEmailsTool`, `GetEmailTool`, `GetThreadTool`, `ListUnreadTool`, and `ListLabelsTool`. `SearchEmailsTool` SHALL accept a `query_scope` restricting the full-text query to the subject or the body, and `GetEmailTool` SHALL accept a `fields` selector mirroring `SearchEmailsTool`'s.

#### Scenario: SearchEmailsTool wraps the search use case
- **WHEN** `SearchEmailsTool` is invoked with query, from, to, subject, date range, label, unread, page, and page_size arguments
- **THEN** it builds a `SearchEmailsQuery`, invokes `SearchEmailsUseCase`, and returns the paginated result

#### Scenario: Search restricts the full-text query to subject or body
- **WHEN** `SearchEmailsTool` is invoked with `query_scope` set to `subject` (or `body`)
- **THEN** the query term is applied to the Gmail subject (or body) field only
- **AND** an invalid `query_scope` maps to an `invalid_input` tool error

#### Scenario: GetEmailTool wraps the get-email use case
- **WHEN** `GetEmailTool` is invoked with an email_id
- **THEN** it invokes `GetEmailUseCase` and returns the email DTO

#### Scenario: GetEmailTool projects requested fields
- **WHEN** `GetEmailTool` is invoked with `fields` (e.g. `["subject", "from", "date"]`)
- **THEN** the result contains only `id` plus the requested fields and omits the body
- **AND** an unknown field maps to an `invalid_input` tool error

#### Scenario: Invalid arguments are rejected
- **WHEN** a read tool is invoked with arguments that violate its input schema
- **THEN** a validation error is returned and no use case is invoked

### Requirement: Search tools
The system SHALL provide a `SemanticSearchTool` that wraps `SemanticSearchUseCase` and exposes each result's Gmail `message_id` so agents can fetch the matched email directly.

#### Scenario: SemanticSearchTool wraps the semantic search use case
- **WHEN** `SemanticSearchTool` is invoked with query, limit, and min_score
- **THEN** it invokes `SemanticSearchUseCase` and returns the scored search results

#### Scenario: Semantic results carry the Gmail message id
- **WHEN** a semantic search result's email resolves from the local repository
- **THEN** the result includes the email's Gmail `message_id`
