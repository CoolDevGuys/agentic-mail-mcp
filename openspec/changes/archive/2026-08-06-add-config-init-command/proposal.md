## Why

First-run setup currently means hand-editing a 30-key `.env` file copied from
`.env.example`: users must know which keys matter, hand-write a valid Fernet
encryption key, and format list/dict values (`[]`, `{}`) correctly — a common
source of setup errors before they ever reach `auth`. An interactive `init`
command removes that friction and gets a new user to a valid configuration in
one guided pass.

## What Changes

- Add a new `agentic-mail-mcp init` subcommand that runs an interactive,
  full guided walkthrough and writes a valid `.env` file.
- **BREAKING**: running `agentic-mail-mcp` with **no subcommand** now prints
  help and exits instead of starting the server. The server must be started
  explicitly with `agentic-mail-mcp serve`. This makes `serve`/`auth`/`init`
  symmetric and prevents an accidental bare run from launching a server. All
  call sites that relied on the bare command (MCP client config examples, the
  HTTP run command, the Docker `CMD`) are updated to use `serve`.
- Prompt through **every** configuration section (Gmail credentials, database +
  cache TTL, railguards, MCP transport, LLM, semantic search, notifications,
  logging), each field showing its default and accepting Enter-to-accept.
- **Auto-generate** the token encryption key
  (`AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY`) when the user doesn't supply
  one, so no user ever hand-writes a secret.
- Validate inputs inline against the same rules as `Settings` (e.g. access level
  ∈ {read_only, read_write}, transport ∈ {stdio, http}, numeric ports/TTL,
  a credentials path that exists) and re-prompt on invalid entries.
- Protect an existing `.env`: detect it, and require explicit confirmation,
  writing a timestamped backup (`.env.bak-<ts>`) before overwriting.
- Emit correctly formatted values, including JSON-encoded list/dict fields
  (`[]`, `{}`) and quoted values where needed, so the result loads cleanly.
- Print next steps on completion (run `auth`, then start the server), and
  respect `--yes`/non-interactive fallback only insofar as needed for safety
  (see design).
- Update `README.md` and `specs/docs/configuration.md` to lead first-run setup
  with `agentic-mail-mcp init`.

## Capabilities

### New Capabilities
- `config-init`: The interactive `init` CLI command that guides a user through
  every configuration section and generates a valid `.env` file, including
  encryption-key generation, input validation, and safe handling of an existing
  file.
- `cli`: Command dispatch behavior for the `agentic-mail-mcp` entry point —
  notably that invoking it with **no subcommand prints help and exits** (rather
  than starting the server), and that `serve`/`auth`/`init` are the recognized
  subcommands. (First time CLI dispatch is specced; the server-start behavior of
  `serve` itself is unchanged.)

### Modified Capabilities
<!-- None. The `settings` schema and env-var contract are unchanged; the wizard
     only writes values that already exist. Doc updates are Impact, not spec
     requirement changes. -->

## Impact

- **Code**: new `agentic_mail_mcp/Bootstrap/config_init.py` (wizard logic, pure
  and testable via injected input/output); `agentic_mail_mcp/Bootstrap/cli.py`
  gains an `init` subparser + handler and changes the no-subcommand branch to
  print help and exit instead of calling `_serve`. No changes to `Settings`
  fields.
- **Breaking call sites** (must switch bare command → `serve`):
  - `Dockerfile` `CMD ["agentic-mail-mcp"]` → `CMD ["agentic-mail-mcp", "serve"]`
    (docker-compose inherits the image `CMD`).
  - `README.md` MCP client config (`"args": ["agentic-mail-mcp"]` and the
    `"command": "agentic-mail-mcp"` pip note) → include `serve`.
  - `README.md` HTTP run command `… agentic-mail-mcp` → `… agentic-mail-mcp serve`.
  - `cli.py` `serve` help text drops the "(default)" note.
- **Tests**: new unit tests driving the wizard with scripted input (accept
  defaults, invalid-then-valid re-prompt, existing-`.env` backup, key
  auto-generation) and a test asserting the no-subcommand invocation prints help
  and does not start the server; keeping Domain/overall coverage floors green.
- **Docs**: `README.md` Quick start + `specs/docs/configuration.md` updated to
  present `init` as the recommended first step and to use `serve` explicitly;
  `.env.example` remains the reference of record and must stay in sync with the
  fields the wizard writes.
- **Dependencies**: none new — uses stdlib `getpass`/`input` and existing
  `cryptography` (already a dependency) for key generation.
