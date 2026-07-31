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

Set environment variables with the `GMAIL_MCP_` prefix, or use a `.env` file:

| Variable | Description | Default |
|---|---|---|
| `GMAIL_MCP_GMAIL_OAUTH_CLIENT_ID` | Google OAuth client ID | (required) |
| `GMAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET` | Google OAuth client secret | (required) |
| `GMAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` | Token encryption key | (required) |
| `GMAIL_MCP_GMAIL_SCOPES` | Gmail API scopes | `https://www.googleapis.com/auth/gmail.modify` |
| `GMAIL_MCP_GMAIL_TOKEN_STORAGE_PATH` | OAuth token file path | `token.json` |
| `GMAIL_MCP_DATABASE_URL` | Database URL | `sqlite+aiosqlite:///./gmail_mcp.db` |
| `GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL` | `read_only` or `read_write` | `owner` |
| `GMAIL_MCP_LLM_PROVIDER` | LLM provider | `openai` |
| `GMAIL_MCP_LLM_MODEL` | LLM model | `gpt-4` |
| `GMAIL_MCP_LLM_API_KEY` | LLM API key | (required for intelligence) |
| `GMAIL_MCP_MCP_HOST` | HTTP host | `127.0.0.1` |
| `GMAIL_MCP_MCP_PORT` | HTTP port | `8080` |
| `GMAIL_MCP_LOGGING_LEVEL` | Log level | `INFO` |

## Usage

Run the server:

```bash
gmail-mcp-server
```

The server supports two transport modes:
- **stdio** (default) — for AI agent consumption
- **HTTP** — on configurable host/port (default: `127.0.0.1:8080`)

### Docker

```bash
docker-compose up --build
```

## MCP Tools

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

## Development

```bash
# Run tests
pytest

# Run linter
ruff check .

# Run type checker
mypy src/
```

## License

MIT
