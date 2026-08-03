## Why

Phases 3 and 4 defined the domain models, ports (GmailGateway, EmailRepository, ThreadRepository, LlmGateway, EmbeddingGateway, VectorSearchRepository, NotificationGateway), and the application use cases that orchestrate them — but every port is still backed only by in-memory test fakes. Nothing talks to Gmail, a database, an LLM, a vector index, or a notification channel. Phase 5 implements the real infrastructure adapters for those ports so the use cases can run against live systems, unblocking the Phase 6 railguards and Phase 7 MCP server that wire everything to AI agents.

## What Changes

- **Gmail Google adapter**: `GmailOAuthProvider` (interactive + headless OAuth2, encrypted refresh-token storage outside the repo), `GmailApiGateway` (implements `GmailGateway` via google-api-python-client with retry + rate limiting), `GmailWatcher` (watch/stop-watch push notifications + webhook callback handling), `GmailHistorySynchronizer` (applies history deltas to the local cache and emits domain events).
- **Gmail persistence**: SQLAlchemy ORM models (Email, Thread, Attachment, Label), domain↔ORM mappers, `SqliteEmailRepository` / `SqliteThreadRepository` implementing the repository ports, and the initial Alembic migration (single `migrations/` dir, `alembic.ini` at repo root). Optional PostgreSQL repository/migration variants sharing the same schema.
- **Intelligence LLM adapter**: `LlamaCppGateway` implementing `LlmGateway` against llama.cpp or an OpenAI-compatible endpoint, configured via Settings (local model path or remote API).
- **Search vector adapter**: `SqliteVssRepository` (default) and `PgVectorRepository` (optional) both implementing `VectorSearchRepository`, plus a shared `BgeEmbeddingGateway` implementing `EmbeddingGateway`. A shared contract test suite runs against both vector backends to guarantee interchangeability.
- **Notification channels adapter**: `WebhookNotificationGateway` (POSTs payloads to configured URLs) and `RedisNotificationGateway` (pub/sub), both implementing `NotificationGateway`.
- New runtime dependencies added as optional extras where heavy (sqlite-vss/vec, pgvector, redis, llama-cpp/openai client, BGE embedding model), and the default `DatabaseConfig` driver aligned to a synchronous SQLite driver to match the synchronous repository ports.
- Integration tests for every adapter (mocked HTTP for Gmail/LLM/webhook, in-memory SQLite, fakeredis for Redis, dockerized PostgreSQL for the PG variants).

## Capabilities

### New Capabilities
- `gmail-google-adapter`: OAuth2 provider with encrypted token storage, `GmailGateway` implementation over the Gmail API with retry/rate-limiting, push-notification watcher, and history synchronizer that emits domain events.
- `gmail-persistence`: SQLAlchemy models, domain↔ORM mappers, SQLite repository implementations of the repository ports, Alembic migrations, and optional PostgreSQL variants.
- `intelligence-llm-adapter`: `LlmGateway` implementation backed by llama.cpp or an OpenAI-compatible API, configurable for local or remote inference.
- `search-vector-adapter`: `EmbeddingGateway` (BGE) plus interchangeable `VectorSearchRepository` implementations for sqlite-vss (default) and pgvector (optional).
- `notification-channels-adapter`: `NotificationGateway` implementations for outbound webhooks and Redis pub/sub.

### Modified Capabilities
<!-- None at the requirement level. The synchronous-SQLite default and new dependency extras are implementation details within the existing `settings`, `project-config`, and `docker` capabilities; the DatabaseConfig sections and dependency lists already permit them. -->

## Impact

- New modules under `src/Gmail/Infrastructure/Google/`, `src/Gmail/Infrastructure/Persistence/SqlAlchemy/` and `.../PostgreSQL/`, `src/Intelligence/Infrastructure/LlamaCpp/`, `src/Search/Infrastructure/SqliteVSS/`, `.../PgVector/` and `.../BGE/`, `src/Notification/Infrastructure/Webhook/` and `.../Redis/` — all currently empty stubs.
- New `migrations/` directory and `alembic.ini` at the repo root; `Common/Infrastructure/Persistence/` gains the SQLAlchemy engine/session factory wiring.
- `pyproject.toml` gains runtime/optional dependencies (google client already present; adds sqlite-vss/vec, pgvector, redis, llama-cpp-python/openai, BGE embeddings) and matching test deps (pytest-httpserver or responses, fakeredis).
- `.env.example` and `Bootstrap/Settings.py` gain adapter configuration keys (LLM endpoint/model path/api key, vector backend selection, embedding model); default DB URL switches to a synchronous SQLite driver.
- New integration-test packages under `tests/integration/` per bounded context; the OAuth token file and any local model artifacts must stay out of the repo (`.gitignore`).
- Depends on the Phase 3 ports and Phase 4 use cases; does not modify them. The railguard framework (Phase 6) and MCP server (Phase 7) remain out of scope.
