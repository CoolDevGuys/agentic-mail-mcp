# cli Specification

## Purpose
Define the top-level command-line interface behavior for `agentic-mail-mcp`, ensuring that invoking the command with no subcommand is safe (prints help, never starts the server) and that the MCP server starts only through the explicit `serve` subcommand.

## Requirements

### Requirement: Default invocation shows help

The `agentic-mail-mcp` command SHALL print its help/usage text and exit without
side effects when invoked with no subcommand. It MUST NOT start the server in
this case.

#### Scenario: No subcommand prints help and does not serve

- **WHEN** `agentic-mail-mcp` is run with no subcommand
- **THEN** the usage/help text is printed
- **AND** the process exits without starting the MCP server

#### Scenario: Help lists the available subcommands

- **WHEN** the no-subcommand help is printed
- **THEN** it lists `serve`, `auth`, `init`, and `verify-auth` as available
  subcommands

### Requirement: Server starts only via the serve subcommand

The CLI SHALL start the MCP server only when the `serve` subcommand is given, so
that starting the server is always explicit.

#### Scenario: serve starts the server

- **WHEN** `agentic-mail-mcp serve` is run with a valid configuration
- **THEN** the MCP server is started using the configured transport
