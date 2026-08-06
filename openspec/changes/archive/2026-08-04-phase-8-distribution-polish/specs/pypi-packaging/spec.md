## ADDED Requirements

### Requirement: License file
The project SHALL include a top-level `LICENSE` file whose license matches the `pyproject.toml` metadata (MIT).

#### Scenario: License present and consistent
- **WHEN** the repository root is inspected
- **THEN** a `LICENSE` file exists and its license matches the `license` field declared in `pyproject.toml`

### Requirement: Distribution metadata
The `pyproject.toml` SHALL carry the metadata required for a PyPI release: name, version, description, `readme`, license, authors, classifiers, and project URLs.

#### Scenario: Metadata is complete
- **WHEN** `pyproject.toml` is read
- **THEN** it declares name, version, description, `readme`, license, authors, classifiers, and `project.urls`

### Requirement: Buildable distribution with console entry point
The project SHALL build a valid source distribution and wheel that expose the `gmail-mcp-server` console entry point.

#### Scenario: Build produces sdist and wheel
- **WHEN** the package is built
- **THEN** a source distribution and a wheel are produced without error

#### Scenario: Entry point is exposed
- **WHEN** the built distribution's metadata is inspected
- **THEN** it declares the `gmail-mcp-server` console script pointing at the MCP server CLI

### Requirement: Documented publish flow
The project SHALL document the release flow to Test-PyPI and then production PyPI.

#### Scenario: Publish steps documented
- **WHEN** the release documentation is read
- **THEN** it describes building and uploading to Test-PyPI followed by production PyPI

### Requirement: Release hygiene
The repository SHALL NOT contain committed secrets or superseded entry-point skeletons: `token.json` and `credentials.json` SHALL be absent and ignored, and the pre-DDD `main.py` and `server.py` skeletons SHALL be removed (or relocated under `examples/`).

#### Scenario: Secrets are absent and ignored
- **WHEN** the repository is inspected
- **THEN** `token.json` and `credentials.json` are not tracked and are listed in `.gitignore`, along with the default token-storage path

#### Scenario: Superseded skeletons removed
- **WHEN** the repository root is inspected
- **THEN** the pre-DDD `main.py` and `server.py` skeletons are no longer present at the root
