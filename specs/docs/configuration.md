# Configuration

> All settings are defined in `agentic_mail_mcp/Bootstrap/Settings.py` and loaded from
> environment variables (prefix `AGENTIC_MAIL_MCP_`) or a `.env` file. See
> `.env.example` for a copy-paste template. This document stays in sync with
> both.

## Quick setup: `agentic-mail-mcp init`

The fastest way to a valid `.env` is the interactive wizard:

```bash
agentic-mail-mcp init
```

It walks through **every** configuration section, showing each field's default —
**press Enter to accept a default**, or type a value to override it. It also:

- **Auto-generates the token encryption key** when you leave that prompt empty,
  so you never hand-write a secret.
- **Validates as you go** (e.g. access level, transport, ports) and re-prompts on
  invalid input, then loads the result through `Settings` before saving — so the
  file it writes is always loadable.
- **Never clobbers an existing `.env`**: it asks first and writes a timestamped
  backup (`.env.bak-<timestamp>`) before overwriting.

When it finishes, run `agentic-mail-mcp auth` (below) and then start the server.

> `.env.example` remains the canonical reference for every key, its default, and
> its purpose. The wizard writes the same keys; the tables further down document
> them in full. You can always edit the generated `.env` by hand afterward.

## How configuration is loaded

Settings come from these sources, **highest priority first**:

1. **Process environment variables** (`AGENTIC_MAIL_MCP_*`) — e.g. exported in a
   shell, a systemd unit, a Docker `environment:`, or an MCP client's `env` block.
2. **A `--env-file PATH`** (or the `AGENTIC_MAIL_MCP_ENV_FILE` variable) — an
   explicit `.env` the server loads on startup, regardless of working directory.
   Real environment variables from step 1 still win over it.
3. **A `.env` file** — read from the server's **current working directory**.
4. **Built-in defaults**.

Two consequences worth internalizing:

- **A `.env` file is never required.** It is just a convenient carrier for the
  same variables. Anything you can put in `.env` you can set as an environment
  variable instead, for either transport.
- **`.env` is resolved relative to the process's working directory**, not to
  where you ran a command. If a program launches the server from some other
  directory, a `.env` sitting in your project folder is simply not seen. This is
  the key difference between the two workflows below.

## Configuration workflows: stdio vs HTTP

The same settings drive both transports; only *how you deliver them* differs.

### What's always needed (both transports)

| Thing | When | Notes |
|---|---|---|
| Google client (`CLIENT_SECRETS_FILE`, or `OAUTH_CLIENT_ID` + `_SECRET`) | at `auth` **and** `serve` | Identifies your OAuth app |
| `GMAIL_TOKEN_ENCRYPTION_KEY` | at `auth` **and** `serve` | The token is encrypted with a key derived from this — it **must be identical** at auth time and serve time, or the server can't decrypt the token |
| `GMAIL_TOKEN_STORAGE_PATH` | at `auth` **and** `serve` | Must point to the **same file** both times (default `token.json`, relative to cwd — set an absolute path to avoid surprises) |
| `agentic-mail-mcp auth` | **once**, up front | Mints the encrypted token. Needs a browser (see [Headless](#7-headless--server-deployment-no-browser) if the server host has none) |

`init` is **optional** — it only generates a `.env` and auto-creates the
encryption key. Skip it if you provide the variables another way.

**Verify auth at any time** with `agentic-mail-mcp verify-auth` (accepts
`--env-file`). It checks the client config and encryption key, then makes a live
Gmail call to confirm the stored token still works, printing the authorized
account on success. It exits `0` on success and non-zero on failure — each
failure says exactly what to fix (configure a client, set the key, run `auth`, or
re-`auth` for an expired/revoked token). The **HTTP server also runs this check
at startup**: on failure it logs a prominent warning with the fix but **still
starts** (stdio startup skips the network check).

### 🧩 stdio — the MCP client launches the server

Here the client spawns `agentic-mail-mcp serve` as a subprocess **and controls
its working directory**, which is usually *not* your project folder — so a
`.env` there won't be found. You have two ways to supply config:

**Option A — point at a `.env` file (recommended).** Pass `--env-file` with an
**absolute** path; the server loads every setting from that file. Run
`agentic-mail-mcp init` first to create it. The `env` block can stay empty:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["agentic-mail-mcp", "serve", "--env-file", "/abs/path/.env"]
    }
  }
}
```

(Equivalently, set `"env": { "AGENTIC_MAIL_MCP_ENV_FILE": "/abs/path/.env" }`.)

**Option B — inline `env` block.** Put the variables directly in the client
config; they become the process environment. No file involved:

```json
{
  "mcpServers": {
    "gmail": {
      "command": "uvx",
      "args": ["agentic-mail-mcp", "serve"],
      "env": {
        "AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE": "/abs/path/credentials.json",
        "AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY": "<same key used at auth>",
        "AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH": "/abs/path/token.json",
        "AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL": "read_only"
      }
    }
  }
}
```

Either way:

1. Get Google credentials (below) and pick an encryption key (or let `init`
   generate one).
2. Run `agentic-mail-mcp auth` **once** with those same values — for Option A,
   the easiest is `agentic-mail-mcp auth --env-file /abs/path/.env`, which reads
   the very same file. This writes the encrypted token to `TOKEN_STORAGE_PATH`.
3. Configure your client as above with the **same** encryption key and token
   path. The client starts the server on demand; you do **not** run `serve`
   yourself.

> Inline `env` values take precedence over the `--env-file`, which in turn takes
> precedence over a `.env` in the working directory — so you can point at a file
> and still override a single value in the `env` block.

### 🌐 HTTP — you launch the server

Here **you** start a long-running process, so you control the working directory.
Both a `.env` and exported environment variables work; pick one.

1. Get Google credentials and either run `agentic-mail-mcp init` (writes `.env`)
   or set the `AGENTIC_MAIL_MCP_*` variables in your service manager /
   `docker-compose`.
2. Run `agentic-mail-mcp auth` **once** (from the same directory / with the same
   variables, so it reads the same client + key).
3. Start the server from that directory (so `.env` is found) or with the
   variables exported:

   ```bash
   AGENTIC_MAIL_MCP_MCP_TRANSPORT=http AGENTIC_MAIL_MCP_MCP_HOST=0.0.0.0 \
   AGENTIC_MAIL_MCP_MCP_PORT=8080 agentic-mail-mcp serve
   ```

   With Docker, set the variables in `environment:` (or mount a `.env` and an
   absolute `TOKEN_STORAGE_PATH`); the token file must be the one produced by
   `auth` (see [Headless](#7-headless--server-deployment-no-browser) to authorize
   on a machine with a browser and copy the token in).

4. **Point your MCP client at the streamable-HTTP endpoint**, which is served at
   the **`/mcp`** path — `http://<host>:<port>/mcp`, by default
   `http://localhost:8080/mcp`:

   ```json
   { "mcpServers": { "gmail": { "type": "http", "url": "http://localhost:8080/mcp" } } }
   ```

   Unlike stdio, config lives with the **server** (steps 1–3), not the client;
   the client only needs the URL.

> **Rule of thumb:** if *something else* starts the server (an MCP client),
> deliver config through its `env` block. If *you* start the server (HTTP,
> systemd, Docker, or `make run`), a `.env` in that working directory — the thing
> `init` writes — is the easy path.

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
   (`./token.json` above). Copy it to the server at the path the server uses.

   > ⚠️ **The token file is binary — transfer it byte-for-byte, never by
   > copy-paste.** Despite the `.json` name it is *not* text: it starts with 16
   > raw random bytes (an encryption salt). Piping it through a clipboard
   > (`cat token.json | pbcopy`) or a chat window corrupts those bytes, and the
   > server then fails with `Stored OAuth token could not be decrypted…` even
   > though the key is correct. Use one of these instead:

   ```bash
   # Best — copies the exact bytes over a secure channel:
   scp ./token.json you@server:/etc/agentic-mail-mcp/token.json
   ```

   ```bash
   # If you must use a clipboard, base64-encode it so it survives as text:
   base64 -i ./token.json | pbcopy                 # on the machine with the token
   # …then on the server, paste where PASTED is:
   echo 'PASTED' | base64 -d > /etc/agentic-mail-mcp/token.json
   ```

   Verify the transfer was exact — the sizes and hashes must match on both
   machines: `wc -c token.json` and `shasum -a 256 token.json` (macOS) /
   `sha256sum token.json` (Linux).

3. On the server, point the same three variables at the copied file and start
   the server normally — no browser, no `auth` step:

   ```bash
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH=/etc/agentic-mail-mcp/token.json
   AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY=<same key as step 1>
   AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE=/etc/agentic-mail-mcp/credentials.json
   ```

4. Confirm auth works on the server before wiring up an agent:

   ```bash
   agentic-mail-mcp --env-file /etc/agentic-mail-mcp/.env verify-auth
   ```

   It should print `Authorized as <account>`. If it reports the token could not
   be decrypted, the transfer corrupted the file (re-copy with `scp`) or the
   encryption key differs between machines.

**Requirements & notes**

- ⚠️ **The token file is binary** (a raw salt prefix + ciphertext). Move it with
  `scp` or base64 — a text copy-paste will corrupt it. See step 2.
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

## Deployment troubleshooting

### Database: "Read-only file system"

```
sqlite3.DatabaseError: ... [Errno 30] Read-only file system: '/path/to/agentic_mail_mcp.db'
```

The SQLite database file must be on a writable filesystem. The default path
(`./agentic_mail_mcp.db`) is relative to the process's working directory, which
for systemd services or containers may be read-only.

**Fix:** Set an absolute path on a writable volume:

```bash
AGENTIC_MAIL_MCP_DATABASE_URL=sqlite:////var/lib/agentic-mail-mcp/agentic_mail_mcp.db
```

The server validates the DB path on startup and exits with a clear error if the
directory is not writable.

### Search returns empty metadata

If `search_emails` returns results with empty `subject`, `from_address`, `date`,
etc. (only `message_id` and `thread_id` populated), this is fixed in the
upcoming patch. The server now fetches full message metadata via
`messages.batchGet` after `messages.list`.

### Stale cache after server restart

After `systemctl restart`, cached list operations (`list_unread`, `find_by_thread_id`)
may return empty results until emails are re-seen. This is fixed in the upcoming
patch: the cache freshness map is now seeded from persisted data on startup.

### Missing sqlite_vec (semantic search unavailable)

```
Semantic search unavailable: No module named 'sqlite_vec'
```

The `sqlite-vec` package is an optional dependency. Install the `search` extra:

```bash
pip install -e ".[search]"
```

For Docker, the image installs the `search` extra by default (upcoming patch). If building
custom images, ensure `pysqlite3-binary` is installed before the package for SQLite
extension loading support on `python:-slim` bases.

### ASGI shutdown error

```
ERROR: ASGI callable returned without completing response.
```

This occurs when `systemctl stop` terminates active SSE streams. The server now
handles SIGTERM gracefully (upcoming patch). For systemd, add a stop timeout:

```ini
[Service]
TimeoutStopSec=30
```

### "Missing session ID" on direct HTTP calls

```json
{"code":-32600,"message":"Bad Request: Missing session ID"}
```

The streamable-HTTP transport requires the MCP **initialize handshake** before
tool calls. Clients must:

1. **POST** `/mcp` with `{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"client","version":"1.0"}}}`
2. Use the `Mcp-Session-Id` header from the response on all subsequent requests

This is expected behavior — the server is not a REST API, it's an MCP server.
Use an MCP client (not raw HTTP) to interact with it. The health check in the
Dockerfile (`socket.connect()`) works because it only tests port connectivity,
not the MCP protocol.
