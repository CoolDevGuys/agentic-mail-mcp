## Why

Phases 4–5 delivered the read use cases and every infrastructure adapter, but the **write path is still unimplemented**: Phase 4 defined the write *command objects* (Forward/Archive/Delete/CreateDraft/SendDraft) and deferred their execution to this phase precisely because writes need safety controls. Phase 6 builds the railguards framework — the read-only-by-default access model, recipient allowlist, action blocklist, rate limits, archive-first policy, and audit trail — and the railguarded write use cases that enforce it. This is the gate that makes it safe to expose write tools to an AI agent in Phase 7.

## What Changes

- **Railguard configuration model**: `AccessLevel` (`read_only` default / `read_write`), `AllowedRecipients`, `BlockedActions`, `RateLimits`, and `ArchiveFirstPolicy`, parsed from `Settings.railguards`. Default is **read_only** when unset.
- **RailguardValidator**: validates a command against the rules (recipient allowlist, action blocklist, rate limit window, archive-first) before execution; returns a `RailguardResult` (allowed/denied + reason) and raises `PermissionError` on violation.
- **Audit log**: an `AuditLog` entry (timestamp, action, email_id, details, correlation_id), an `AuditLogRepository` (with a SQLite implementation + migration), and an `AuditLogHandler` domain-event subscriber that records every write operation.
- **Railguarded write use cases** (executing the Phase-4 command objects): `ForwardEmailUseCase` (recipient allowlist + rate limit, original as RFC822 attachment, emits `EmailForwarded`), `ArchiveEmailUseCase` (removes INBOX label, emits `EmailArchived`), `DeleteEmailUseCase` (soft-delete default, permanent only when allowed + archive-first satisfied, emits `EmailDeleted`), and draft-first sending via `CreateDraftUseCase` / `SendDraftUseCase`.
- **GmailGateway draft methods**: `create_draft`, `send_draft`, and `delete_draft` (Gmail `users.drafts` API) plus draft DTOs — draft-first sending has no gateway support today.
- **Settings**: the `railguards` section gains `archive_first_policy`; `access_level` becomes `read_only`/`read_write` with a `read_only` default.

## Capabilities

### New Capabilities
- `railguards`: railguard configuration model with a read-only default, and `RailguardValidator` enforcing recipient allowlist, action blocklist, rate limits, and archive-first policy, returning `RailguardResult` and raising `PermissionError` on violation.
- `audit-log`: `AuditLog` entry, `AuditLogRepository` (SQLite-backed) and `AuditLogHandler` event subscriber that persists an audit record for every write operation, including correlation ids.

### Modified Capabilities
- `gmail-application`: adds the railguarded write use cases — `ForwardEmailUseCase`, `ArchiveEmailUseCase`, `DeleteEmailUseCase`, `CreateDraftUseCase`, `SendDraftUseCase` — consuming the Phase-4 command objects and emitting the corresponding domain events.
- `gmail-domain`: `GmailGateway` port gains draft operations (`create_draft`, `send_draft`, `delete_draft`) and their DTOs.
- `gmail-google-adapter`: `GmailApiGateway` implements the new draft operations against the Gmail `users.drafts` API.
- `settings`: the `railguards` section adds `archive_first_policy` and the `access_level` field uses `read_only`/`read_write` values with a `read_only` default.

## Impact

- New modules under `src/Common/Railguards/` (config model, validator, result) and `src/Common/Audit/` (audit entry, repository port, handler), with a SQLite `AuditLogRepository` and ORM model/migration under the persistence layer.
- New railguarded write use cases under `src/Gmail/Application/UseCases/`; new draft methods on the `GmailGateway` port and `GmailApiGateway`.
- `Settings.railguards` gains `archive_first_policy`; `access_level` default changes to `read_only` (**BREAKING** for any deployment relying on the current `owner` default — writes are now denied until explicitly enabled). `.env.example` and `specs/docs/configuration.md` updated.
- New Alembic migration for the `audit_log` table; `specs/docs/data-model.md` and `events.md` updated; CHANGELOG entry.
- Depends on Phase 4 command objects, Phase 3 domain events (`EmailForwarded`/`EmailArchived`/`EmailDeleted`), `PermissionError` (Phase 2), the `Clock` (rate-limit windows), and the Phase 5 Gmail gateway/persistence. MCP tool exposure of these write use cases is Phase 7 and out of scope.
