## Context

Phase 3 defined the ports and Phase 4 the use cases, all **synchronous** (no `async def` anywhere in the repository/gateway protocols or use cases). The application layer is fully exercised by in-memory fakes under `tests/fakes/ports.py`. Phase 5 supplies the real adapters behind those ports without touching the archived Phase 3/4 contracts.

Two facts shape the work:
1. **The ports are synchronous.** `DatabaseConfig.url` currently defaults to `sqlite+aiosqlite:///…` (async), which cannot back a synchronous repository. This must be reconciled.
2. **The project default is SQLite, PostgreSQL optional** (per the plan's scope notes). Every adapter has a default (SQLite/sqlite-vss/local-or-remote LLM/webhook) and heavier or optional backends gated behind extras.

The adapters are the first code in the system that performs I/O, so retry, rate limiting, secret handling, and error translation (technical exceptions → domain errors at the boundary) all land here.

## Goals / Non-Goals

**Goals:**
- Implement every Phase 3 port with at least one real adapter, keeping the port contracts unchanged.
- Keep SQLite the zero-config default; make PostgreSQL and pgvector strictly optional via extras.
- Guarantee the two `VectorSearchRepository` implementations are interchangeable via a shared contract test suite.
- Never persist or log secrets in plaintext: encrypted refresh tokens at rest, redaction filter for logs.
- Translate infrastructure failures into domain errors (`NotFoundError`, etc.) at the adapter boundary.

**Non-Goals:**
- Making the ports/use cases async (would break the archived Phase 4 contract) — revisit only if a later phase requires it.
- Railguard enforcement (Phase 6) and MCP wiring (Phase 7).
- Production model hosting / GPU tuning for the LLM and embedding models.

## Decisions

**1. Synchronous SQLAlchemy, synchronous SQLite driver.**
Because the repository ports are synchronous, use the synchronous SQLAlchemy engine with the stdlib `sqlite3` driver (`sqlite:///…`) rather than `aiosqlite`. Change the `DatabaseConfig` default URL accordingly and update `.env.example`. Alternative — make repositories async — rejected: it ripples into the archived Phase 4 use cases and the Phase 7 MCP handlers, a far larger and contract-breaking change. A single synchronous session factory lives in `Common/Infrastructure/Persistence/`.

**2. One schema, one migrations directory, driver-agnostic DDL.**
A single `migrations/` directory with `alembic.ini` at the repo root serves both SQLite and PostgreSQL. The ORM models use portable column types; PG-specific concerns (e.g., pgvector columns) live only in the vector adapter, not the core Email/Thread schema. This matches plan 5.2/5.3 and avoids divergent schemas.

**3. GmailApiGateway wraps the Google client and returns gateway DTOs, never ORM/domain objects.**
The adapter implements `GmailGateway`, returning the plain gateway dataclasses (`GmailMessage`, `GmailListResponse`, …) already defined in the port. Retries use exponential backoff on 429/5xx; a token-bucket limiter caps request rate. HTTP is fully mockable so tests need no network. Mapping gateway DTOs → domain entities stays in the existing `EmailMapper`/`ThreadMapper`.

**4. OAuth tokens encrypted at rest, stored outside the repo.**
`GmailOAuthProvider` persists refresh tokens to `Settings.gmail.token_storage_path` (default outside the project dir, e.g. `~/.config/agentic-mail-mcp/`), encrypted with `Settings.gmail.token_encryption_key` (symmetric, e.g. Fernet). Token values are never logged (relies on the Bootstrap logging redaction filter). Supports both interactive browser flow and headless pre-authorized tokens.

**5. `VectorSearchRepository` interchangeability enforced by a shared contract test.**
sqlite-vss (default) and pgvector (optional) implement the same port. A single parametrized contract-test module runs the identical assertions against both backends (index → search → score ordering → delete → count), so either can be swapped without changing callers. The `BgeEmbeddingGateway` is shared by both and produces vectors matching `dimension()`.

**6. LLM adapter is provider-flexible behind one gateway.**
`LlamaCppGateway` targets either a local llama.cpp model (path from Settings) or an OpenAI-compatible HTTP endpoint (base URL + key from Settings), selected by config. It returns the port's `LlmResponse` (text, model, usage). Remote calls are mocked in tests; no model download is required to run the suite.

**7. Notification adapters are thin and best-effort.**
`WebhookNotificationGateway` POSTs JSON via httpx; `RedisNotificationGateway` uses redis pub/sub. Both implement `send`/`publish` returning `bool` (already the port contract) so the Phase-4 use cases' log-on-failure behavior works unchanged. Webhooks mocked with a local HTTP server; Redis tested with fakeredis.

**8. Heavy/optional dependencies behind extras.**
sqlite-vss/vec, pgvector, redis, llama-cpp-python/openai, and the BGE embedding library are declared as optional extras (e.g. `[postgresql]`, `[llm]`, `[search]`, `[notifications]`) so a minimal install stays lean; the default path (SQLite + sqlite-vss + remote LLM + webhook) pulls only what it needs.

## Risks / Trade-offs

- **Sync driver diverges from the current async default** → One-line `DatabaseConfig` default change + `.env.example` update; documented in tasks. No port/use-case changes.
- **sqlite-vss availability/build** → sqlite-vss can be finicky to install across platforms; if it proves unreliable, `sqlite-vec` is a drop-in alternative behind the same adapter interface. The port abstracts the choice.
- **Gmail API quota/rate limits in tests** → All Gmail tests mock the HTTP transport; no live calls. Real quota tuning is deferred to runtime config.
- **Token encryption key management** → If the key is absent/rotated, stored tokens become unreadable; adapter fails fast with a clear domain error rather than logging the token.
- **PostgreSQL/pgvector require Docker** → PG integration tests are marked and skipped when Docker is unavailable, so the default CI path (SQLite) stays green.

## Migration Plan

Greenfield adapters filling existing empty stubs; the only change to prior code is the `DatabaseConfig` default URL (async→sync SQLite) and additive Settings keys — both backward compatible via env overrides. Initial Alembic migration creates the schema from scratch; no data migration. Delivered per bounded context (Gmail Google → Gmail persistence → Intelligence → Search → Notification), each independently testable. `.gitignore` updated to exclude the token file, the local DB file, and any model artifacts.

## Open Questions

- sqlite-vss vs sqlite-vec as the default vector backend — decide during 5.5 based on install reliability on the target platforms; the adapter interface hides the choice.
- Whether the `GmailHistorySynchronizer` should own persistence (write-through to repositories) or only emit events for a separate handler — leaning write-through then emit, revisit if it couples too tightly.
- Default embedding model size (BGE-small vs BGE-base) — pick the smallest that meets the 768-dim expectation used in tests, configurable via Settings.
