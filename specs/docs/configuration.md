# Configuration

> All settings are defined in `src/Bootstrap/Settings.py` and loaded from
> environment variables (prefix `GMAIL_MCP_`) or a `.env` file. See
> `.env.example` for a copy-paste template. This document stays in sync with
> both.

## gmail

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `oauth_client_id` | `GMAIL_MCP_GMAIL_OAUTH_CLIENT_ID` | `""` | Google OAuth client id |
| `oauth_client_secret` | `GMAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET` | `""` | Google OAuth client secret |
| `scopes` | `GMAIL_MCP_GMAIL_SCOPES` | `gmail.modify` | OAuth scopes |
| `token_storage_path` | `GMAIL_MCP_GMAIL_TOKEN_STORAGE_PATH` | `token.json` | Where the encrypted refresh token is stored; set outside the repo in production (e.g. `~/.config/gmail-mcp-server/`) |
| `token_encryption_key` | `GMAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` | `""` | Secret used to encrypt the token at rest (any string; a Fernet key is derived from it). Required to store tokens |

## database

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `url` | `GMAIL_MCP_DATABASE_URL` | `sqlite:///./gmail_mcp.db` | SQLAlchemy URL. **Synchronous** driver — the repositories are synchronous. Use `postgresql+psycopg2://…` for PostgreSQL |
| `driver` | `GMAIL_MCP_DATABASE_DRIVER` | `sqlite` | Informational driver name |

## railguards

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `access_level` | `GMAIL_MCP_RAILGUARDS_ACCESS_LEVEL` | `owner` | Write-access gate (Phase 6) |
| `allowed_recipients` | `GMAIL_MCP_RAILGUARDS_ALLOWED_RECIPIENTS` | `[]` | Forwarding allowlist |
| `blocked_actions` | `GMAIL_MCP_RAILGUARDS_BLOCKED_ACTIONS` | `[]` | Blocked actions |
| `rate_limits` | `GMAIL_MCP_RAILGUARDS_RATE_LIMITS` | `{}` | Per-action rate limits |

## mcp

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `server_name` | `GMAIL_MCP_MCP_SERVER_NAME` | `Gmail-MCP` | MCP server name |
| `host` | `GMAIL_MCP_MCP_HOST` | `127.0.0.1` | HTTP transport host |
| `port` | `GMAIL_MCP_MCP_PORT` | `8080` | HTTP transport port |

## llm

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `provider` | `GMAIL_MCP_LLM_PROVIDER` | `openai` | `openai` (OpenAI-compatible HTTP) or `llamacpp` (local model) |
| `model` | `GMAIL_MCP_LLM_MODEL` | `gpt-4` | Model name |
| `api_key` | `GMAIL_MCP_LLM_API_KEY` | `""` | API key for the remote endpoint |
| `base_url` | `GMAIL_MCP_LLM_BASE_URL` | `""` | OpenAI-compatible base URL; empty uses the official OpenAI URL |
| `model_path` | `GMAIL_MCP_LLM_MODEL_PATH` | `""` | Local llama.cpp model path (used when `provider=llamacpp`) |

## search

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `backend` | `GMAIL_MCP_SEARCH_BACKEND` | `sqlite_vss` | Vector backend: `sqlite_vss` (implemented via sqlite-vec) or `pgvector` |
| `embedding_model` | `GMAIL_MCP_SEARCH_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | BGE embedding model |
| `embedding_dimension` | `GMAIL_MCP_SEARCH_EMBEDDING_DIMENSION` | `384` | Embedding vector dimension |

## notifications

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `webhook_url` | `GMAIL_MCP_NOTIFICATIONS_WEBHOOK_URL` | `""` | Outbound webhook URL |
| `redis_url` | `GMAIL_MCP_NOTIFICATIONS_REDIS_URL` | `""` | Redis URL for pub/sub |

## logging

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `level` | `GMAIL_MCP_LOGGING_LEVEL` | `INFO` | Log level |
| `json_format` | `GMAIL_MCP_LOGGING_JSON_FORMAT` | `true` | JSON structured logs with secret redaction |

## Optional dependency extras

The default stack (SQLite + sqlite-vec + OpenAI-compatible LLM + webhook) needs
only the base dependencies. Heavier or optional backends live behind extras:

- `postgresql` — psycopg2-binary, pgvector
- `search` — sqlite-vec, sentence-transformers
- `notifications` — redis
- `llm` — llama-cpp-python (local inference)
