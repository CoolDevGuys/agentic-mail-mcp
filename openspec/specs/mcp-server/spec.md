# mcp-server Specification

## Purpose
TBD - created by archiving change phase-7-mcp-server. Update Purpose after archive.
## Requirements
### Requirement: MCP server bootstrap
The system SHALL provide an MCP server that is assembled from the dependency container and integrated with the application `Lifespan`, starting and stopping cleanly.

#### Scenario: Server builds from the container
- **WHEN** the MCP server is created with the dependency container
- **THEN** it resolves its settings and registered services from the container and exposes a runnable server instance

#### Scenario: Server integrates the application lifespan
- **WHEN** the MCP server starts
- **THEN** it runs within the `Bootstrap/Lifespan.py` context so startup (DB pool, OAuth token) and shutdown (flush, close) hooks execute around the server lifecycle

#### Scenario: Server stops cleanly
- **WHEN** the MCP server is shut down
- **THEN** the lifespan shutdown completes and no resources are left open

### Requirement: Configurable transport
The MCP server SHALL support a configurable transport, defaulting to `stdio` and selecting HTTP when configured via `Settings.mcp`.

#### Scenario: Default transport is stdio
- **WHEN** the server is created with no transport override
- **THEN** it uses the `stdio` transport

#### Scenario: HTTP transport when configured
- **WHEN** `Settings.mcp` selects HTTP with a host and port
- **THEN** the server binds the HTTP transport to that host and port

### Requirement: Category-grouped tool registry
The system SHALL provide a tool registry that registers each tool with a name, an AI-agent-friendly description, and a JSON-Schema input schema, grouped by category (`read`, `write`, `intelligence`, `search`).

#### Scenario: Tools expose valid schemas
- **WHEN** a tool is registered
- **THEN** it has a name, a non-empty description, and a valid JSON-Schema input schema

#### Scenario: Tools are grouped by category
- **WHEN** the registry is inspected
- **THEN** each registered tool is associated with one of the categories read, write, intelligence, or search

### Requirement: Write tools gated by access level at registration
The tool registry SHALL read `Settings.railguards.access_level` at registration time and SHALL NOT register any write-category tool when the access level is `read_only`, so write tools are absent from the exposed tool list rather than only denied at execution.

#### Scenario: Write tools absent when read-only
- **WHEN** the registry is built with `access_level` = `read_only`
- **THEN** no write-category tool (ForwardEmail, ArchiveEmail, DeleteEmail, CreateDraft, SendDraft, AddLabel) is present in the registry

#### Scenario: All tools present when read-write
- **WHEN** the registry is built with `access_level` = `read_write`
- **THEN** the read, write, intelligence, and search tools are all registered

#### Scenario: Read tools always present
- **WHEN** the registry is built with `access_level` = `read_only`
- **THEN** the read, intelligence, and search tools are still registered

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

### Requirement: Write tools with railguard enforcement
The system SHALL provide write tools that each wrap a single railguarded write use case: `ForwardEmailTool`, `ArchiveEmailTool`, `DeleteEmailTool`, `CreateDraftTool`, `SendDraftTool`, and `AddLabelTool`.

#### Scenario: Write tool wraps its use case
- **WHEN** `ForwardEmailTool` is invoked with email_id, to, subject, body, and include_original
- **THEN** it builds a `ForwardEmailCommand`, invokes `ForwardEmailUseCase`, and returns the result

#### Scenario: Railguard denial surfaces as a tool error
- **WHEN** a write use case raises `PermissionError` due to a railguard denial
- **THEN** the tool returns a structured tool error carrying the denial reason and does not raise an unhandled exception

### Requirement: Intelligence tools
The system SHALL provide intelligence tools that each wrap a single intelligence use case: `SummarizeEmailTool`, `ClassifyEmailTool`, `SuggestReplyTool`, `ExtractActionItemsTool`, `DailyDigestTool`, and `WeeklyDigestTool`.

#### Scenario: SummarizeEmailTool wraps the summarize use case
- **WHEN** `SummarizeEmailTool` is invoked with an email_id
- **THEN** it invokes `SummarizeEmailUseCase` and returns the summary DTO

#### Scenario: DailyDigestTool wraps the daily digest use case
- **WHEN** `DailyDigestTool` is invoked with a date
- **THEN** it invokes `DailyDigestUseCase` and returns the digest DTO

### Requirement: Search tools
The system SHALL provide a `SemanticSearchTool` that wraps `SemanticSearchUseCase` and exposes each result's Gmail `message_id` so agents can fetch the matched email directly.

#### Scenario: SemanticSearchTool wraps the semantic search use case
- **WHEN** `SemanticSearchTool` is invoked with query, limit, and min_score
- **THEN** it invokes `SemanticSearchUseCase` and returns the scored search results

#### Scenario: Semantic results carry the Gmail message id
- **WHEN** a semantic search result's email resolves from the local repository
- **THEN** the result includes the email's Gmail `message_id`

### Requirement: Structured tool results
Every MCP tool SHALL produce real structured content in its `CallToolResult` (unwrapped), so agents can consume the payload as an object without parsing a JSON string returned as text.

#### Scenario: Tool results carry structured content
- **WHEN** a registered tool handler returns its result dictionary
- **THEN** the MCP SDK derives an output schema for it (the handler's return annotation is `dict[str, Any]`, not a bare `dict`)
- **AND** the call result carries the result as a structured object rather than only as a JSON-encoded text payload

### Requirement: Tool error mapping
Every tool SHALL map domain errors to structured MCP tool errors rather than propagating unhandled exceptions, covering at least `PermissionError`, `NotFoundError`, and `ValidationError`.

#### Scenario: Not found maps to a tool error
- **WHEN** a use case raises `NotFoundError`
- **THEN** the tool returns a structured tool error indicating the resource was not found

#### Scenario: Validation failure maps to a tool error
- **WHEN** a use case or input parsing raises `ValidationError`
- **THEN** the tool returns a structured tool error describing the invalid input

### Requirement: MCP resources
The system SHALL expose MCP resources for account info (connected account and access level), watch status (Gmail push-notification state), and index status (vector-index statistics).

#### Scenario: Account info resource reports access level
- **WHEN** the account-info resource is read
- **THEN** it returns the connected account details and the current `access_level`

#### Scenario: Watch status resource reports push state
- **WHEN** the watch-status resource is read
- **THEN** it returns the current Gmail push-notification status

#### Scenario: Index status resource reports statistics
- **WHEN** the index-status resource is read
- **THEN** it returns the vector-search index statistics (e.g. document count)

### Requirement: MCP prompts
The system SHALL provide pre-built prompts that guide AI agents to use the server effectively, including at least a search-strategy prompt and an email-management workflow prompt, each renderable.

#### Scenario: Prompt renders
- **WHEN** a registered prompt is rendered with its expected arguments
- **THEN** a complete prompt string is produced with no unresolved placeholders

