## MODIFIED Requirements

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
