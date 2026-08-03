## 1. Dependencies & Settings

- [x] 1.1 Add runtime/optional dependencies to pyproject.toml: sqlite-vss (or sqlite-vec), redis, llama-cpp-python/openai client, BGE embedding lib; PostgreSQL/pgvector under the [postgresql] extra; test deps (pytest-httpserver or responses, fakeredis)
- [x] 1.2 Change DatabaseConfig default URL to a synchronous SQLite driver (sqlite:///…) and add adapter config keys (llm base_url/api_key/model_path, vector backend selection, embedding model) to Bootstrap/Settings.py
- [x] 1.3 Update .env.example with the new keys; add token file, local DB file, and model artifacts to .gitignore

## 2. Persistence Foundation

- [x] 2.1 Implement the synchronous SQLAlchemy engine + session factory in Common/Infrastructure/Persistence/
- [x] 2.2 Define SQLAlchemy ORM models for Email, Thread, Attachment, Label with portable column types
- [x] 2.3 Implement domain↔ORM mappers (Email/Thread/Attachment/Label)
- [x] 2.4 Write tests for mapper round-trips (domain → ORM → domain preserves fields)

## 3. Gmail Persistence (SQLite)

- [x] 3.1 Implement SqliteEmailRepository (find_by_id, find_by_gmail_message_id, find_by_thread_id, search, list_unread, save, delete)
- [x] 3.2 Implement SqliteThreadRepository (find_by_id, find_by_gmail_thread_id, save, delete)
- [x] 3.3 Add alembic.ini at repo root and the initial migration creating all four tables
- [x] 3.4 Write integration tests with in-memory SQLite (save/find, gmail-id lookup, list_unread limit, missing→None, thread round-trip)
- [x] 3.5 Write a shared repository contract test suite reusable by SQLite and PostgreSQL

## 4. Gmail Google Adapter

- [x] 4.1 Implement GmailOAuthProvider (interactive + headless flows, encrypted token storage outside repo, decrypt-failure raises domain error, never logs tokens)
- [x] 4.2 Implement GmailApiGateway for all GmailGateway methods using google-api-python-client, returning gateway DTOs
- [x] 4.3 Add retry-with-backoff on 429/5xx and a rate limiter around API calls
- [x] 4.4 Implement GmailWatcher (watch/stop-watch + webhook callback handling)
- [x] 4.5 Implement GmailHistorySynchronizer (apply deltas, write-through to repository, emit domain events, idempotent per history id)
- [x] 4.6 Write tests with mocked HTTP transport for all gateway methods, watcher, and synchronizer

## 5. Intelligence LLM Adapter

- [x] 5.1 Implement LlamaCppGateway implementing LlmGateway, config-selectable between local model path and OpenAI-compatible endpoint
- [x] 5.2 Map provider responses to LlmResponse (text, model, usage) and translate provider errors to a domain error
- [x] 5.3 Write tests with mocked LLM responses (remote endpoint path, error path)

## 6. Search Vector Adapter

- [x] 6.1 Implement BgeEmbeddingGateway implementing EmbeddingGateway (embed length == dimension(), deterministic for identical input)
- [x] 6.2 Implement SqliteVssRepository (default) implementing VectorSearchRepository
- [x] 6.3 Implement PgVectorRepository (optional) implementing VectorSearchRepository
- [x] 6.4 Write a shared parametrized VectorSearchRepository contract test suite; run it against both backends
- [x] 6.5 Write tests for BgeEmbeddingGateway (dimension match, determinism)

## 7. Notification Channels Adapter

- [x] 7.1 Implement WebhookNotificationGateway (POST via httpx, True on success / False on failure, never raises)
- [x] 7.2 Implement RedisNotificationGateway (pub/sub, True on delivery / False on connection failure)
- [x] 7.3 Write tests: mocked HTTP server for webhooks, fakeredis for Redis

## 8. Optional PostgreSQL & Verification

- [x] 8.1 Implement PostgreSQL repository variants and PG-specific migration; run the shared repository contract test against them (marked/skipped without Docker)
- [x] 8.2 Wire adapters into the DependencyContainer defaults (SQLite + sqlite-vss + LLM + webhook)
- [x] 8.3 Run full test suite (unit + integration) and confirm coverage floors hold (≥90% Domain/, ≥80% overall)
- [x] 8.4 Run ruff and mypy across new infrastructure modules and fix findings
- [x] 8.5 Update specs/docs (data-model.md for the ORM schema, configuration.md/events.md as needed) and CHANGELOG.md
