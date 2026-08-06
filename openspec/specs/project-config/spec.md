# project-config Specification

## Purpose
Defines the project packaging and configuration contract: metadata, build backend, dependencies, optional extras, and the console entry point.

## Requirements

### Requirement: pyproject.toml exists with complete metadata
The project SHALL have a pyproject.toml file containing name (agentic-mail-mcp), version, description, authors, license, and Python 3.11+ classifiers.

#### Scenario: Project metadata is present
- **WHEN** pyproject.toml is read
- **THEN** project.name equals "agentic-mail-mcp"
- **THEN** project.requires-python includes ">=3.11"

### Requirement: Build system uses hatchling
The project SHALL use hatchling as its build backend.

#### Scenario: Build backend is configured
- **WHEN** pyproject.toml is parsed
- **THEN** build-system.requires includes "hatchling"
- **THEN** build-system.backend equals "hatchling"

### Requirement: Core dependencies are declared
The project SHALL declare runtime dependencies: mcp, google-api-python-client, google-auth-oauthlib, pydantic, pydantic-settings, aiosqlite, sqlalchemy, alembic, httpx, python-dotenv.

#### Scenario: All core deps listed
- **WHEN** project.dependencies is read
- **THEN** each required package appears in the list

### Requirement: Optional extras are available
The project SHALL provide [postgresql] extra (asyncpg, psycopg2) and [dev] extra (pytest, pytest-asyncio, pytest-cov, ruff, mypy).

#### Scenario: Extras install correctly
- **WHEN** pip install agentic-mail-mcp[postgresql] executes
- **THEN** asyncpg and psycopg2 are installed
- **WHEN** pip install agentic-mail-mcp[dev] executes
- **THEN** pytest, ruff, and mypy are installed

### Requirement: Console script entry point
The project SHALL define a console script "agentic-mail-mcp" pointing to the MCP server CLI module.

#### Scenario: Entry point is registered
- **WHEN** the package is installed
- **THEN** the agentic-mail-mcp command is available in PATH
