## ADDED Requirements

### Requirement: Init subcommand generates configuration file

The CLI SHALL provide an `init` subcommand that interactively collects
configuration and writes a `.env` file loadable by `Settings.from_env()`.

#### Scenario: Init writes a loadable .env

- **WHEN** a user runs `agentic-mail-mcp init` and accepts the guided prompts
- **THEN** a `.env` file is written whose keys use the `AGENTIC_MAIL_MCP_` prefix
- **AND** loading it via `Settings.from_env()` succeeds without error

#### Scenario: Init is discoverable

- **WHEN** `agentic-mail-mcp --help` is shown
- **THEN** `init` is listed as an available subcommand alongside `serve` and `auth`

### Requirement: Full guided walkthrough across all sections

The wizard SHALL prompt for every configuration section (gmail, database,
railguards, mcp, llm, search, notifications, logging), displaying each field's
default and accepting an empty input to keep that default.

#### Scenario: Empty input keeps the default

- **WHEN** the user presses Enter at a prompt without typing a value
- **THEN** the field is written with its documented default value

#### Scenario: All sections are covered

- **WHEN** the wizard completes
- **THEN** the generated `.env` contains at least the required keys for the
  gmail, database, railguards, mcp, llm, search, notifications, and logging
  sections

### Requirement: Token encryption key auto-generation

The wizard SHALL generate a cryptographically strong token encryption key when
the user does not supply one, so no secret is ever hand-written.

#### Scenario: Key generated when omitted

- **WHEN** the user leaves the token encryption key prompt empty
- **THEN** `AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` is written with a
  generated high-entropy value (not a placeholder)

#### Scenario: User-supplied key is preserved

- **WHEN** the user types a value at the token encryption key prompt
- **THEN** that exact value is written and no key is generated

### Requirement: Input validation with re-prompt

The wizard SHALL validate inputs against the same constraints as `Settings` and
re-prompt on invalid input rather than writing an invalid file.

#### Scenario: Invalid enum re-prompts

- **WHEN** the user enters a value outside the allowed set for a constrained
  field (e.g. access level not in `read_only`/`read_write`, transport not in
  `stdio`/`http`)
- **THEN** the wizard reports the problem and prompts again for the same field
- **AND** does not proceed until a valid value is entered

#### Scenario: Non-numeric value for a numeric field re-prompts

- **WHEN** the user enters a non-numeric value for a numeric field (e.g. port or
  cache TTL)
- **THEN** the wizard re-prompts for that field

### Requirement: Safe handling of an existing configuration file

The wizard SHALL NOT silently overwrite an existing `.env`. It SHALL require
explicit confirmation and preserve the previous file as a timestamped backup.

#### Scenario: Existing file is backed up before overwrite

- **WHEN** a `.env` already exists and the user confirms overwriting it
- **THEN** the previous file is copied to a timestamped backup (e.g.
  `.env.bak-<timestamp>`) before the new file is written

#### Scenario: Declining overwrite aborts without changes

- **WHEN** a `.env` already exists and the user declines to overwrite it
- **THEN** the wizard exits without modifying the existing `.env`

### Requirement: Correctly serialized values

The wizard SHALL emit values in the format the settings loader expects,
including JSON-encoded list and dict fields.

#### Scenario: List and dict fields are JSON-encoded

- **WHEN** list/dict-typed fields (allowed recipients, blocked actions, rate
  limits, scopes) are written with their defaults
- **THEN** they appear as valid JSON (`[]`, `{}`, or a JSON array) that
  `Settings.from_env()` parses without error

### Requirement: Post-completion guidance

On success the wizard SHALL tell the user the next steps to reach a running
server.

#### Scenario: Next steps are printed

- **WHEN** the wizard finishes writing `.env`
- **THEN** it prints the path written and instructs the user to run
  `agentic-mail-mcp auth` and then start the server
