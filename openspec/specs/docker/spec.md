# docker Specification

## Purpose
Container image and compose setup for building and running the MCP server.
## Requirements
### Requirement: Dockerfile with Python 3.11 slim
The Dockerfile SHALL be a multi-stage build: a builder stage that installs build dependencies and produces a wheel, and a `python:3.11-slim` runtime stage that installs only the built package, runs as a non-root user, and contains no build toolchain.

#### Scenario: Dockerfile stages
- **WHEN** the Dockerfile is parsed
- **THEN** it defines a builder stage that builds the package and a `python:3.11-slim` runtime stage
- **THEN** the runtime stage installs the built package and runs as a non-root user

#### Scenario: Runtime image excludes build toolchain
- **WHEN** the runtime stage is inspected
- **THEN** it copies the built artifact from the builder rather than installing build tools

### Requirement: docker-compose with services
The docker-compose.yml SHALL define a agentic-mail-mcp service and an optional postgres service for testing.

#### Scenario: Services defined
- **WHEN** docker-compose.yml is parsed
- **THEN** agentic-mail-mcp and postgres services exist

### Requirement: Health check
The MCP server container SHALL include a health check on the MCP server port.

#### Scenario: Health check configured
- **WHEN** the container runs
- **THEN** a health check probes the MCP port periodically

### Requirement: .dockerignore
The project SHALL include a .dockerignore excluding .venv, __pycache__, and .git.

#### Scenario: Exclusions present
- **WHEN** .dockerignore is read
- **THEN** .venv, __pycache__, and .git are listed

### Requirement: Multi-architecture build
The image SHALL be buildable for both `linux/amd64` and `linux/arm64`.

#### Scenario: Multi-arch build documented and supported
- **WHEN** the release documentation is read
- **THEN** it describes building the image for `linux/amd64` and `linux/arm64` (e.g. via `docker buildx`)

#### Scenario: Dockerfile is architecture-agnostic
- **WHEN** the Dockerfile is parsed
- **THEN** it pins no architecture-specific base image or dependency that would prevent an arm64 or amd64 build

