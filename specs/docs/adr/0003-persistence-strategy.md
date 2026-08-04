# 0003 — SQLite Default, PostgreSQL Optional

Status: accepted

Context: The server caches Gmail data (emails, threads, labels), an audit log, and a vector index for semantic search. Deployments range from a single developer running the server as a local stdio subprocess to a shared, always-on HTTP deployment. A local subprocess should need zero external services; a larger deployment should be able to use a managed relational database. Forcing PostgreSQL on every user would make the common case (one person, one mailbox) needlessly heavy; hard-coding SQLite would cap the larger case.

Decision: **SQLite is the default persistence backend; PostgreSQL is an optional, opt-in alternative** behind the same repository ports. Repository and vector-search ports are defined in each context's `Domain/`; the SQLite adapters (`sqlite-vec` for vectors) are the default implementations and require no extra dependencies. PostgreSQL adapters (`psycopg2`, `pgvector`) live behind the `postgresql` extra and are selected via `Settings.database.url` / `Settings.search.backend`. A single Alembic `migrations/` directory is shared across both backends. Contract tests run the same suite against both vector adapters to guarantee interchangeability. Repositories use synchronous drivers to match the synchronous use cases.

Consequences:

- **Easier:** The default install runs with no external services — `pip install .` and go. Switching to PostgreSQL is a config change plus an extra, not a code change, because both satisfy the same ports. Tests use in-memory SQLite for speed.
- **Harder:** Two backends must be kept behaviorally equivalent, which requires contract tests and discipline about backend-specific SQL. The vector story depends on `sqlite-vec` being installable (prebuilt wheels) for the default path.
- **Future:** Another store (e.g. a hosted vector DB) can be added as a new adapter behind the existing ports. If the async need arises, the ports can gain async variants without changing domain logic.
