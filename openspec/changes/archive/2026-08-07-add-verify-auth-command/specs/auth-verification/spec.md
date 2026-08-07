## ADDED Requirements

### Requirement: On-demand auth verification command

The CLI SHALL provide a `verify-auth` subcommand that checks the Google
credentials and stored token and reports whether the server can authenticate to
Gmail. It accepts the shared `--env-file` option.

#### Scenario: Valid token reports the account and exits zero

- **WHEN** `agentic-mail-mcp verify-auth` runs with resolvable client config, an
  encryption key, and a stored token that Gmail accepts
- **THEN** it prints the authorized account email address
- **AND** exits with status `0`

#### Scenario: verify-auth is discoverable

- **WHEN** `agentic-mail-mcp --help` is shown
- **THEN** `verify-auth` is listed among the available subcommands

### Requirement: The check performs a live Gmail call

The verification SHALL confirm the token by making a live Gmail API call (a
profile lookup), not merely by checking that a token file exists — so an
expired or revoked token is detected.

#### Scenario: Present-but-rejected token is reported invalid

- **WHEN** a token file exists but Gmail rejects it (expired or revoked)
- **THEN** the check fails with a message stating the token is no longer valid
  and to re-run `agentic-mail-mcp auth`

### Requirement: Actionable failure reporting per stage

The check SHALL identify which prerequisite failed and how to fix it, and the
`verify-auth` command SHALL exit non-zero on any failure.

#### Scenario: Missing client configuration

- **WHEN** neither a client secrets file nor an OAuth client id/secret is
  configured
- **THEN** the check fails identifying the missing Google client configuration
- **AND** `verify-auth` exits non-zero

#### Scenario: Missing token

- **WHEN** client config and encryption key are present but no token has been
  stored
- **THEN** the check fails instructing the user to run `agentic-mail-mcp auth`
- **AND** `verify-auth` exits non-zero

### Requirement: HTTP startup preflight warns but continues

When the server starts on the HTTP transport, it SHALL run the auth
verification and, on failure, log a prominent warning describing the problem and
fix, but SHALL still start the server.

#### Scenario: Invalid auth at HTTP startup does not stop the server

- **WHEN** the HTTP server starts and the auth check fails
- **THEN** a warning describing the failure and remediation is logged
- **AND** the server still starts and begins serving

#### Scenario: stdio startup does not run the network check

- **WHEN** the server starts on the stdio transport
- **THEN** the live Gmail auth check is not performed at startup
