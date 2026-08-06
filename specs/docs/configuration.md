# Configuration

> All settings are defined in `agentic_mail_mcp/Bootstrap/Settings.py` and loaded from
> environment variables (prefix `AGENTIC_MAIL_MCP_`) or a `.env` file. See
> `.env.example` for a copy-paste template. This document stays in sync with
> both.

## Getting your Google credentials (OAuth)

> **You bring your own Google app.** This server is a local tool, not a hosted
> service — there is no central app to sign into and **no Google verification to
> wait for**. You create your own OAuth client in *your* Google Cloud project,
> and your credentials and token never leave your machine. Because the app only
> ever authorizes you (its own owner / test user), Google's verification process
> does not apply.

The server talks to Gmail on your behalf using a Google OAuth **client** (the
`client_id` / `client_secret`, downloaded as a `credentials.json`) plus a
**refresh token** obtained once through a consent screen. You create the client
in Google Cloud; the server obtains and stores the token. This is a one-time,
~5-minute setup.

### 1. Create a Google Cloud project

1. Open the [Google Cloud Console](https://console.cloud.google.com/).
2. Click the project picker (top bar) → **New Project** → name it (e.g.
   `agentic-mail-mcp`) → **Create**, then select it.

### 2. Enable the Gmail API

1. Go to **APIs & Services → Library**
   ([direct link](https://console.cloud.google.com/apis/library/gmail.googleapis.com)).
2. Search **Gmail API** → **Enable**.

### 3. Configure the OAuth consent screen

1. Go to **APIs & Services → OAuth consent screen**.
2. Choose **External** (unless you're on Google Workspace and want Internal) →
   **Create**.
3. Fill the required fields (app name, your support email, developer email) →
   **Save and Continue**.
4. **Scopes**: you can leave this empty here — the server requests
   `https://www.googleapis.com/auth/gmail.modify` at authorization time.
5. **Test users**: add the Gmail address(es) you'll connect. While the app is in
   "Testing" mode, only listed test users can authorize — that's fine for
   personal use and avoids Google's app-verification review.

### 4. Create an OAuth client ID

1. Go to **APIs & Services → Credentials → Create Credentials → OAuth client ID**.
2. **Application type: Desktop app** (this is important — the server uses the
   installed-app / loopback flow) → **Create**.
3. **Download JSON** — this is your `credentials.json`.

Point the server at it (recommended — no copying secrets around):

```bash
AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE=/path/to/credentials.json
```

*Or*, if you prefer, set the id/secret directly instead:

```bash
AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID=<client id>.apps.googleusercontent.com
AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET=<client secret>
```

### 5. Set a token encryption key

The refresh token is encrypted at rest. Provide any secret string (a Fernet key
is derived from it):

```bash
AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
```

### 6. Authorize (one-time consent)

Run the interactive authorization once:

```bash
agentic-mail-mcp auth        # or: make auth
```

A browser window opens; sign in with a **test user** account and grant access.
You may see an **"unverified app"** screen — that's expected for your own app;
click *Advanced → Go to … (unsafe)* to continue. The encrypted refresh token is
written to `token_storage_path` and reused on every subsequent start — you won't
be prompted again unless the token is revoked or deleted. If you launch the
server before authorizing, its tools are still listed but calling one returns a
clear *"run `agentic-mail-mcp auth`"* error.

> **Keep the token from expiring.** While your app's publishing status is
> **"Testing"**, Google expires refresh tokens after **7 days**, so you'd re-run
> `agentic-mail-mcp auth` weekly. To avoid that, set the OAuth consent screen to
> **"In production"** (*APIs & Services → OAuth consent screen → Publish app*).
> For your own single-user app this needs **no Google verification** — the
> unverified-app screen just remains. Tokens then persist until revoked.

### 7. Headless / server deployment (no browser)

`agentic-mail-mcp auth` opens a browser and runs a **loopback redirect** on
`localhost`, so it can't complete on a headless box (a container, a VPS, a CI
runner). You don't authorize on the server at all — you **authorize once on a
machine that has a browser, then copy the token to the server.** The refresh
token is portable and self-contained: after the first authorization the server
never needs a browser again, it just refreshes silently.

> **Why not a copy-paste code or "device" flow?** Google **removed** the old
> out-of-band console flow in 2022, and its Device Authorization Grant **does not
> permit Gmail scopes**. Copying the token (below) is the supported path for
> Gmail on a headless host.

**Steps**

1. **On a machine with a browser** (e.g. your laptop), authorize using the
   **same `credentials.json`** and the **same
   `AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY`** you'll run on the server:

   ```bash
   AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE=/path/to/credentials.json \
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY="<the server's key>" \
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH=./token.json \
     agentic-mail-mcp auth
   ```

2. This writes the **encrypted** token file to `token_storage_path`
   (`./token.json` above). Copy it to the server at the path the server uses,
   over a secure channel:

   ```bash
   scp ./token.json you@server:/etc/agentic-mail-mcp/token.json
   ```

3. On the server, point the same three variables at the copied file and start
   the server normally — no browser, no `auth` step:

   ```bash
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH=/etc/agentic-mail-mcp/token.json
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY=<same key as step 1>
   AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE=/etc/agentic-mail-mcp/credentials.json
   ```

**Requirements & notes**

- ⚠️ **The encryption key must match** on both machines. The token is
  Fernet-encrypted with a key derived from
  `AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY`; a different key on the server
  can't decrypt it (`Stored OAuth token could not be decrypted…`).
- The token file is encrypted, but still transfer it over a secure channel
  (`scp`/secrets manager) and mount it read-only — never bake it into an image
  or commit it.
- **Set the consent screen to "In production"** (see the expiry note above)
  before doing this. In "Testing" mode the copied refresh token still expires
  after 7 days, forcing a re-copy every week.
- **Docker:** mount the token (and `credentials.json`) as a volume/secret rather
  than copying into the image, e.g.
  `-v /etc/agentic-mail-mcp:/secrets:ro` with the paths above pointing into
  `/secrets`.

### Scopes

`gmail.modify` (the default) covers read, label, archive, **trash** (soft
delete), and draft/send — everything the tools do except one thing:
**permanent delete** (`delete_email` with `permanent=true`) needs the broader
`https://mail.google.com/` scope. Under `gmail.modify` a permanent delete
returns a 403; soft delete (the default) always works. Permanent delete is also
blocked by the railguards unless you explicitly allow it, so most deployments
never need the broader scope.

For a strictly read-only deployment you can narrow it to
`https://www.googleapis.com/auth/gmail.readonly` — but note that write **tools**
are already gated off by `railguards.access_level=read_only` (the default), so
you usually don't need to change the scope.

### Security notes

- Treat the client secret and the stored token as secrets. `token.json` and
  `credentials.json` are git-ignored; keep the token outside the repo in
  production (e.g. `~/.config/agentic-mail-mcp/token.json`).
- If a credential leaks, rotate it in the Cloud Console (**Credentials →** your
  client **→ Reset secret**) and re-authorize.

## gmail

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `client_secrets_file` | `AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE` | `""` | Path to the OAuth client JSON you download from Google Cloud (recommended). Takes precedence over `client_id`/`client_secret` |
| `oauth_client_id` | `AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID` | `""` | Google OAuth client id |
| `oauth_client_secret` | `AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET` | `""` | Google OAuth client secret |
| `scopes` | `AGENTIC_MAIL_MCP_GMAIL_SCOPES` | `gmail.modify` | OAuth scopes |
| `token_storage_path` | `AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH` | `token.json` | Where the encrypted refresh token is stored; set outside the repo in production (e.g. `~/.config/agentic-mail-mcp/`) |
| `token_encryption_key` | `AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` | `""` | Secret used to encrypt the token at rest (any string; a Fernet key is derived from it). Required to store tokens |

## database

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `url` | `AGENTIC_MAIL_MCP_DATABASE_URL` | `sqlite:///./agentic_mail_mcp.db` | SQLAlchemy URL. **Synchronous** driver — the repositories are synchronous. Use `postgresql+psycopg2://…` for PostgreSQL |
| `driver` | `AGENTIC_MAIL_MCP_DATABASE_DRIVER` | `sqlite` | Informational driver name |
| `cache_ttl_seconds` | `AGENTIC_MAIL_MCP_DATABASE_CACHE_TTL_SECONDS` | `900` | Read-through email cache TTL. Cache stores **metadata only** (never bodies); single reads are live. Gmail is the source of truth (see [ADR 0007](adr/0007-persistence-read-through-cache.md)) |

## railguards

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `access_level` | `AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL` | `read_only` | Master write gate: `read_only` (default) denies all writes; `read_write` enables them subject to the other rules |
| `allowed_recipients` | `AGENTIC_MAIL_MCP_RAILGUARDS_ALLOWED_RECIPIENTS` | `[]` | Forwarding allowlist; matches a full address or a domain (`@example.com`). Empty = no restriction |
| `blocked_actions` | `AGENTIC_MAIL_MCP_RAILGUARDS_BLOCKED_ACTIONS` | `[]` | Blocked actions (e.g. `permanent_delete`) |
| `rate_limits` | `AGENTIC_MAIL_MCP_RAILGUARDS_RATE_LIMITS` | `{}` | Max operations per action within the trailing 1-hour window (e.g. `{"forward": 50}`) |
| `archive_first_policy` | `AGENTIC_MAIL_MCP_RAILGUARDS_ARCHIVE_FIRST_POLICY` | `false` | When true, an email must be archived before it can be permanently deleted |

> **Writes are denied by default.** With `access_level=read_only` (the default), every forward/archive/delete/draft operation is refused. Set `read_write` to enable writes.

## mcp

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `server_name` | `AGENTIC_MAIL_MCP_MCP_SERVER_NAME` | `Agentic-Mail-MCP` | MCP server name |
| `transport` | `AGENTIC_MAIL_MCP_MCP_TRANSPORT` | `stdio` | Transport for AI-agent harnesses: `stdio` (default) or `http` (streamable HTTP, served on `host:port`) |
| `host` | `AGENTIC_MAIL_MCP_MCP_HOST` | `127.0.0.1` | HTTP transport host |
| `port` | `AGENTIC_MAIL_MCP_MCP_PORT` | `8080` | HTTP transport port |

## llm

> **The LLM is optional (caller-first).** The calling agent is itself an LLM, so
> per-email reasoning (summarize, classify, draft a reply, extract action items)
> ships as **MCP prompts** the agent runs on data it fetches with `get_email` —
> no server-side inference, no added latency, no key required. Configuring an LLM
> only enables the **digest tools** (`daily_digest` / `weekly_digest`), which
> map-reduce over many emails. See [ADR 0006](adr/0006-caller-first-intelligence.md).

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `provider` | `AGENTIC_MAIL_MCP_LLM_PROVIDER` | `openai` | `openai` (OpenAI-compatible HTTP) or `llamacpp` (local model) |
| `model` | `AGENTIC_MAIL_MCP_LLM_MODEL` | `gpt-4` | Model name |
| `api_key` | `AGENTIC_MAIL_MCP_LLM_API_KEY` | `""` | API key. Empty = no LLM (digests off, per-email stays caller-side) |
| `base_url` | `AGENTIC_MAIL_MCP_LLM_BASE_URL` | `""` | OpenAI-compatible base URL; empty uses the official OpenAI URL |
| `model_path` | `AGENTIC_MAIL_MCP_LLM_MODEL_PATH` | `""` | Local llama.cpp model path (used when `provider=llamacpp`) |
| `internal_tools` | `AGENTIC_MAIL_MCP_LLM_INTERNAL_TOOLS` | `false` | Also expose per-email summarize/classify/reply/action-items as **server-side tools** (adds latency; needs an LLM). Default keeps them as prompts |

## search

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `backend` | `AGENTIC_MAIL_MCP_SEARCH_BACKEND` | `sqlite_vss` | Vector backend: `sqlite_vss` (implemented via sqlite-vec) or `pgvector` |
| `embedding_model` | `AGENTIC_MAIL_MCP_SEARCH_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | BGE embedding model |
| `embedding_dimension` | `AGENTIC_MAIL_MCP_SEARCH_EMBEDDING_DIMENSION` | `384` | Embedding vector dimension |

## notifications

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `webhook_url` | `AGENTIC_MAIL_MCP_NOTIFICATIONS_WEBHOOK_URL` | `""` | Outbound webhook URL |
| `redis_url` | `AGENTIC_MAIL_MCP_NOTIFICATIONS_REDIS_URL` | `""` | Redis URL for pub/sub |

## logging

| Key | Env var | Default | Purpose |
|---|---|---|---|
| `level` | `AGENTIC_MAIL_MCP_LOGGING_LEVEL` | `INFO` | Log level |
| `json_format` | `AGENTIC_MAIL_MCP_LOGGING_JSON_FORMAT` | `true` | JSON structured logs with secret redaction |

## Optional dependency extras

The default stack (SQLite + sqlite-vec + OpenAI-compatible LLM + webhook) needs
only the base dependencies. Heavier or optional backends live behind extras:

- `postgresql` — psycopg2-binary, pgvector
- `search` — sqlite-vec, sentence-transformers
- `notifications` — redis
- `llm` — llama-cpp-python (local inference)
