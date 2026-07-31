## ADDED Requirements

### Requirement: Dockerfile with Python 3.11 slim
The Dockerfile SHALL use python:3.11-slim as base, copy pyproject.toml, install dependencies, copy source, and run as non-root user.

#### Scenario: Dockerfile stages
- **WHEN** the Dockerfile is parsed
- **THEN** it uses python:3.11-slim base
- **THEN** it runs as a non-root user

### Requirement: docker-compose with services
The docker-compose.yml SHALL define a gmail-mcp-server service and an optional postgres service for testing.

#### Scenario: Services defined
- **WHEN** docker-compose.yml is parsed
- **THEN** gmail-mcp-server and postgres services exist

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
