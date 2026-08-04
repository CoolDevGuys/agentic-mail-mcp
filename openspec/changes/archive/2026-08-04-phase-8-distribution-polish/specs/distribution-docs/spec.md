## ADDED Requirements

### Requirement: Complete README
The `README.md` SHALL document the project so an integrator can adopt it without reading the source: a project/architecture overview, installation via pip and Docker, configuration, the complete list of MCP tools with descriptions, the railguards security model, an AI-agent integration example over stdio, and contributing guidance.

#### Scenario: README covers installation and usage
- **WHEN** `README.md` is read
- **THEN** it documents pip and Docker installation, a stdio integration example, and points to the configuration reference

#### Scenario: README lists the tools and the safety model
- **WHEN** `README.md` is read
- **THEN** it lists the available MCP tools with descriptions and describes the railguards model (read-only default, allowlist, rate limits, archive-first, draft-first)

### Requirement: MCP API reference
The project SHALL provide `specs/docs/api.md` documenting the MCP surface: every tool (name, description, input schema, output shape), every resource, every prompt, and the structured error-response format.

#### Scenario: Every registered tool is documented
- **WHEN** `specs/docs/api.md` is read
- **THEN** each MCP tool exposed by the server appears with its input schema and output shape

#### Scenario: Resources, prompts, and errors are documented
- **WHEN** `specs/docs/api.md` is read
- **THEN** the account/watch/index resources, the search-strategy and email-management prompts, and the structured error format are documented

### Requirement: Domain-model catalog
The project SHALL provide `specs/docs/domain-model.md` cataloguing the bounded contexts, entities and their relationships, value objects, domain events, and aggregate boundaries.

#### Scenario: Domain catalog is complete
- **WHEN** `specs/docs/domain-model.md` is read
- **THEN** it documents the bounded contexts, the aggregates and value objects, and the domain events catalog

### Requirement: Architecture decision records
The project SHALL provide architecture decision records for the four foundational decisions — DDD with vertical slicing, SQLite-default/PostgreSQL-optional persistence, the railguards write-safety model, and MCP stdio as the default transport — each following the Status/Context/Decision/Consequences template.

#### Scenario: The four decisions are recorded
- **WHEN** the `specs/docs/adr/` directory is listed
- **THEN** ADRs exist for DDD + vertical slicing, SQLite/PostgreSQL persistence, the railguards model, and MCP stdio transport

#### Scenario: Each ADR follows the template
- **WHEN** an architecture ADR is read
- **THEN** it contains Status, Context, Decision, and Consequences sections
