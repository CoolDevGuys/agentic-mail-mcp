# Gmail MCP Server

A Model Context Protocol (MCP) server that exposes Gmail operations for AI agents. Designed to be consumed by AI agent frameworks to programmatically interact with Gmail accounts in a safe, controlled manner.

## Features

- **Email Operations** — Search, read, forward, archive, delete, draft, and label emails
- **Intelligence** — LLM-powered summaries, classifications, reply suggestions, action item extraction, and daily/weekly digests
- **Semantic Search** — Vector-based email search using natural language queries
- **Notifications** — Real-time event handling via webhooks or Redis
- **Railguards** — Safety controls including read-only defaults, recipient allowlists, action blocklists, rate limiting, archive-first delete policy, draft-first sending, and audit logging

## Requirements

- Python 3.11+
- Google OAuth credentials (client ID and secret from Google Cloud Console)
- LLM API key (for intelligence features, default: OpenAI)

## Installation

```bash
pip install .
```

With PostgreSQL support:

```bash
pip install ".[postgresql]"
```

With development dependencies:

```bash
pip install ".[dev]"
```

## Configuration

Set environment variables with the `GMAIL_MCP_` prefix, or use a `.env` file
(copy `.env.example`). The table below covers the essentials; **every** setting,
with defaults and purpose, is documented in
[`specs/docs/configuration.md`](specs/docs/configuration.md).

| Variable | Description | Default |
|---|---|---|
| `GMAIL_MCP_GMAIL_OAUTH_CLIENT_ID` | Google OAuth client ID | (required) |
| `GMAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET` | Google OAuth client secret | (required) |
| `GMAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` | Secret used to encrypt the stored token | (required to store tokens) |
| `GMAIL_MCP_GMAIL_TOKEN_STORAGE_PATH` | Encrypted token file path (set outside the repo in prod) | `token.json` |
| `GMAIL_MCP_DATABASE_URL` | SQLAlchemy URL (synchronous driver) | `sqlite:///./gmail_mcp.db` |
| `GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL` | `read_only` or `read_write` — **writes denied by default** | `read_only` |
| `GMAIL_MCP_LLM_PROVIDER` | `openai` (HTTP) or `llamacpp` (local) | `openai` |
| `GMAIL_MCP_LLM_API_KEY` | LLM API key | (required for intelligence) |
| `GMAIL_MCP_MCP_TRANSPORT` | `stdio` (default) or `http` | `stdio` |
| `GMAIL_MCP_MCP_HOST` / `GMAIL_MCP_MCP_PORT` | HTTP transport bind address | `127.0.0.1` / `8080` |

## Usage

Run the server:

```bash
gmail-mcp-server
```

The server supports two transport modes:
- **stdio** (default) — for AI agent consumption
- **HTTP** — on configurable host/port (default: `127.0.0.1:8080`)

### AI agent integration (stdio)

Most agent harnesses launch the server as a subprocess and speak MCP over
stdio. A typical MCP client config entry:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "gmail-mcp-server",
      "env": {
        "GMAIL_MCP_GMAIL_OAUTH_CLIENT_ID": "...",
        "GMAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET": "...",
        "GMAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY": "...",
        "GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL": "read_only"
      }
    }
  }
}
```

The agent then discovers the tools, resources, and prompts described in
[`specs/docs/api.md`](specs/docs/api.md). Start with `read_only` and enable
`read_write` deliberately once you understand the railguards.

### Docker

```bash
docker-compose up --build
```

## MCP Tools

Full input/output schemas, resources, prompts, and error formats are in the
[MCP API reference](specs/docs/api.md).

### Read Tools (always available)

- `search_emails` — Search emails by subject, sender, recipient, date range, labels, attachments, unread status
- `get_email` — Read a specific email by ID
- `get_thread` — Read a conversation thread
- `list_unread` — List unread emails
- `list_labels` — List labels (system, user, or all)

### Write Tools (require `read_write` access)

- `forward_email` — Forward an email (recipient allowlist enforced)
- `archive_email` — Archive an email or thread
- `delete_email` — Delete an email (trash by default, archive-first policy)
- `create_draft` — Create a draft for review
- `send_draft` — Send a reviewed draft
- `add_label` — Add a label to an email

### Intelligence Tools

- `summarize_email` — LLM-generated email summary
- `classify_email` — Classify by category and priority
- `suggest_reply` — LLM-suggested reply draft
- `extract_action_items` — Extract action items from email
- `daily_digest` — Daily email digest
- `weekly_digest` — Weekly email digest

### Search Tools

- `semantic_search` — Natural language vector search

## Project Structure

```
src/
  Bootstrap/           CLI, Settings, Logging, Lifespan, DI Container
  Common/              Shared domain primitives
  Gmail/               Gmail bounded context
  Intelligence/        LLM-powered email analysis
  Search/              Semantic/vector search
  Notification/        Event notifications
  MCP/                 MCP server, tools, resources, prompts
tests/
  unit/                Unit tests
  integration/         Integration tests
  fakes/               Test doubles
```

## Railguards (security model)

Writes are **denied by default**. Safety is layered so an AI agent cannot mutate
a mailbox unless a human deliberately enables it:

- **Access level** — `read_only` (default) or `read_write`. The master switch.
  Under `read_only`, write tools are **not even registered** with the MCP server
  (defense in depth), so the agent never sees them — not merely blocked at call
  time.
- **Recipient allowlist** — forwarding is restricted to configured addresses or
  domains (`@example.com`).
- **Rate limits** — per-action caps within a trailing 1-hour window
  (e.g. `{"forward": 50}`).
- **Archive-first policy** — an email must be archived before it can be
  permanently deleted; deletes are soft (Trash) by default.
- **Draft-first sending** — the agent creates a draft for human review;
  `send_draft` is a separate, explicit step.
- **Audit log** — every write is recorded (action, email id, correlation id).

A railguard denial surfaces to the agent as a structured `permission_denied`
error, never as an unhandled exception. See the
[railguards configuration](specs/docs/configuration.md#railguards) and
[ADR 0004](specs/docs/adr/0004-railguards-write-safety.md).

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/
```

## Contributing

- The architecture (DDD + vertical slicing) and key decisions are recorded as
  [ADRs](specs/docs/adr/); read them before adding a bounded context or changing
  a boundary.
- Changes follow the OpenSpec workflow under `openspec/` — propose a change,
  generate its spec deltas, implement, then archive.
- Keep the tiered coverage floors green (≥90% on `Domain/`, ≥80% overall) and
  ensure `ruff check` and `mypy src/` pass before opening a PR.

## License

Released under the [MIT License](LICENSE).
