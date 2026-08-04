## 1. Railguard Configuration Model

- [x] 1.1 Update `Settings.railguards`: `access_level` uses `read_only`/`read_write` (default `read_only`), add `archive_first_policy`; update `.env.example`
- [x] 1.2 Implement the railguard config model in `src/Common/Railguards/` (AccessLevel, AllowedRecipients with address/domain matching, BlockedActions, RateLimits, ArchiveFirstPolicy) built from Settings
- [x] 1.3 Write tests for config parsing, validation, and default-is-read_only-when-unset

## 2. RailguardValidator

- [x] 2.1 Implement RailguardResult (allowed/denied + reason)
- [x] 2.2 Implement RailguardValidator.validate(command): read-only master switch, recipient allowlist, action blocklist, rate limits (windowed, clock-injected), archive-first; raises PermissionError on violation
- [x] 2.3 Write tests for all rule combinations and edge cases (read-only denies all, allowlist by address/domain, empty allowlist, blocked action, rate-limit window boundaries, archive-first)

## 3. Audit Log

- [x] 3.1 Implement AuditLog entry (timestamp, action, email_id, details, correlation_id) and AuditLogRepository port in `src/Common/Audit/`
- [x] 3.2 Implement SQLite AuditLogRepository (ORM model + Alembic migration for `audit_log`)
- [x] 3.3 Implement AuditLogHandler subscribing to write events (EmailForwarded/EmailArchived/EmailDeleted + draft events), persisting an entry with correlation id
- [x] 3.4 Write tests: audit trail completeness, correlation ids, per-event persistence

## 4. GmailGateway Draft Operations

- [x] 4.1 Add draft DTOs and `create_draft` / `send_draft` / `delete_draft` to the GmailGateway port
- [x] 4.2 Implement the draft methods in GmailApiGateway against `users.drafts` (create/send/delete) with retry + rate limiting
- [x] 4.3 Extend the test fake Gmail service and write gateway tests for the draft methods

## 5. Railguarded Write Use Cases

- [x] 5.1 Implement ForwardEmailUseCase (validate recipient + rate limit, build RFC822-attached forward, send via gateway, emit EmailForwarded)
- [x] 5.2 Write tests for ForwardEmailUseCase (allowed → EmailForwarded published with correct payload, blocked recipient, rate limit exceeded)
- [x] 5.3 Implement ArchiveEmailUseCase (validate action, remove INBOX via modify_message, emit EmailArchived)
- [x] 5.4 Write tests for ArchiveEmailUseCase (single email, thread, blocked action; EmailArchived published)
- [x] 5.5 Implement DeleteEmailUseCase (soft-delete default; permanent only when allowed + archive-first satisfied; emit EmailDeleted)
- [x] 5.6 Write tests for DeleteEmailUseCase (soft delete, permanent blocked, archive-first enforcement; EmailDeleted published)
- [x] 5.7 Implement CreateDraftUseCase (create draft, return draft_id, no send) and SendDraftUseCase (send reviewed draft)
- [x] 5.8 Write tests for draft creation, sending, deletion, and read-only denial

## 6. Verification & Docs

- [x] 6.1 Wire the RailguardValidator, audit handler, and write use cases into the DI container defaults; register AuditLogHandler on the event bus
- [x] 6.2 Run full unit + integration suite; confirm coverage floors hold (≥90% Domain/, ≥80% overall)
- [x] 6.3 Run ruff and mypy across new modules and fix findings
- [x] 6.4 Update `specs/docs/configuration.md` (read_only default, archive_first_policy), `data-model.md` (audit_log table), `events.md`, and CHANGELOG (note the breaking access_level default change)
