# Data Model

> Persistence schema for the Gmail bounded context. The synchronous SQLAlchemy
> models live in `agentic_mail_mcp/Gmail/Infrastructure/Persistence/SqlAlchemy/Models/` and
> are created by the initial Alembic migration (`migrations/versions/0001`).
> A single portable schema serves SQLite (default) and PostgreSQL (optional).

Timestamps use `UtcDateTime` (see `agentic_mail_mcp/Common/Infrastructure/Persistence/database.py`),
which normalizes values to timezone-aware UTC on write and read so behavior is
identical across SQLite and PostgreSQL.

## Table: `emails`

Aggregate root for a single email. Labels, recipients, and attachment ids are
stored as JSON since they are value collections owned by the aggregate.

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | Primary key (domain UUID) |
| `message_id` | String(255) | Gmail message id; unique index `ix_emails_message_id` |
| `thread_id` | String(255) | Gmail thread id; index `ix_emails_thread_id` |
| `snippet` | Text | |
| `subject` | Text | |
| `from_address` | String(320) | Nullable |
| `to_addresses` | JSON | List of address strings |
| `date_sent` | UtcDateTime | Nullable |
| `is_read` | Boolean | |
| `labels` | JSON | List of label strings |
| `body` | Text | |
| `attachments` | JSON | List of attachment ids |
| `attached_messages` | JSON | List of `{subject, from_address, date_sent, body}` — the original(s) of a forward (nested `message/rfc822` parts). Added by migration `0003` |
| `is_trashed` | Boolean | |

## Table: `threads`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | Primary key (domain UUID) |
| `thread_id` | String(255) | Gmail thread id; unique index `ix_threads_thread_id` |
| `snippet` | Text | |
| `subject` | Text | |
| `participants` | JSON | List of participant strings |
| `email_entries` | JSON | Ordered list of `{email_id, date_sent}` preserving thread order |
| `last_updated` | UtcDateTime | Nullable |
| `is_read` | Boolean | |

## Table: `attachments`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | Primary key (domain UUID) |
| `file_name` | String(1024) | |
| `mime_type` | String(255) | |
| `size_bytes` | Integer | |
| `attachment_id` | String(255) | Gmail attachment id |
| `download_url` | Text | |

## Table: `labels`

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | Primary key (domain UUID) |
| `label_id` | String(255) | Gmail label id; index `ix_labels_label_id` |
| `name` | String(255) | |
| `color` | String(64) | |
| `type` | String(32) | `system` or `user` |

## Table: `audit_log`

Records every write operation (forward, archive, delete) for the railguards
audit trail. Created by migration `0002`.

| Column | Type | Notes |
|---|---|---|
| `id` | String(36) | Primary key (domain UUID) |
| `action` | String(64) | Operation performed; index `ix_audit_log_action` |
| `timestamp` | UtcDateTime | When the operation occurred |
| `correlation_id` | String(64) | Ties the entry to the originating operation; index `ix_audit_log_correlation_id` |
| `email_id` | String(36) | Nullable; the affected email's domain id |
| `details` | JSON | Operation-specific metadata (e.g. `forwarded_to`) |

## Vector index (search context)

Embeddings are **not** stored in the relational schema above. The
`VectorSearchRepository` implementations own their own storage:
- **sqlite-vec** (default): a `vec0` virtual table plus a `documents` table
  keyed by rowid (`agentic_mail_mcp/Search/Infrastructure/SqliteVec/`).
- **pgvector** (optional): a `search_documents` table with a `vector` column
  (`agentic_mail_mcp/Search/Infrastructure/PgVector/`).

## Migrations

`alembic.ini` sits at the repo root; migrations live in `migrations/`. Apply
with `alembic upgrade head`. The database URL comes from
`Settings.database.url` (or an injected url via `config.attributes` in tests).
