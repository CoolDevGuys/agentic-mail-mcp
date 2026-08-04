# e2e-tests Specification

## Purpose
TBD - created by archiving change phase-8-distribution-polish. Update Purpose after archive.
## Requirements
### Requirement: End-to-end MCP tool-flow test
The project SHALL provide an end-to-end test that drives the assembled MCP server through a full tool flow — search, read, forward, archive, delete — against a mocked Gmail API.

#### Scenario: Read/write flow succeeds end-to-end
- **WHEN** the E2E test invokes search → get → forward → archive → delete through the MCP server against a mocked Gmail API under read-write access
- **THEN** each tool call succeeds and the mocked Gmail API records the corresponding operations

### Requirement: End-to-end railguard enforcement
The end-to-end suite SHALL assert railguard enforcement at the MCP boundary — write tools are unavailable under read-only access and denials surface as structured tool errors under read-write.

#### Scenario: Read-only hides write tools end-to-end
- **WHEN** the server is assembled with read-only access and its tool list is requested
- **THEN** no write-category tool is present

#### Scenario: Railguard denial surfaces as a structured error
- **WHEN** a write tool is invoked end-to-end and a railguard denies it
- **THEN** the tool call returns a structured error carrying the denial reason

### Requirement: Container health-check smoke test
The project SHALL provide a smoke test that builds the Docker image, starts the container, and verifies its health check passes; the test MAY be skipped when Docker is unavailable.

#### Scenario: Container starts and reports healthy
- **WHEN** the image is built and the container is started with HTTP transport
- **THEN** the health check reports the container healthy

#### Scenario: Test skips without Docker
- **WHEN** Docker is not available in the environment
- **THEN** the container smoke test is skipped rather than failing

