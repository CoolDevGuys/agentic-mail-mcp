## Context

Phase 4 shipped the write command objects (`ForwardEmailCommand`, `ArchiveEmailCommand`, `DeleteEmailCommand`, `CreateDraftCommand`, `SendDraftCommand`) with no handlers, deliberately deferring execution until safety controls existed. Phase 5 shipped the `GmailApiGateway` (send/modify/trash/delete) and SQLite persistence. Phase 2 provides `PermissionError` and the `Clock`; Phase 3 provides `EmailForwarded`/`EmailArchived`/`EmailDeleted` events and the in-memory `EventBus`. The current `RailguardsConfig` (`access_level="owner"`, allowed_recipients, blocked_actions, rate_limits) is a placeholder from Phase 1.

Two gaps must be closed here: there is **no policy layer** guarding writes, and the `GmailGateway` has **no draft support** (draft-first sending is a core safety feature).

## Goals / Non-Goals

**Goals:**
- Deny writes by default (`access_level=read_only`) so an unconfigured deployment cannot mutate a mailbox.
- Enforce recipient allowlist, action blocklist, rate limits, and archive-first policy uniformly, in one validator, before any gateway call.
- Record every write in a durable audit trail with a correlation id.
- Implement the five write use cases and the draft-first flow, each emitting its domain event only after the gateway call succeeds.

**Non-Goals:**
- Exposing these use cases as MCP tools (Phase 7) — including the defense-in-depth of not *registering* write tools when `read_only`.
- Server-side Gmail filter rules (explicitly out of V1 scope).
- Undo/rollback of executed writes beyond the soft-delete (trash) default.

## Decisions

**1. Read-only by default; `access_level` is the master switch.**
`RailguardConfig.access_level` defaults to `read_only`. The validator denies *every* write command when read-only, regardless of other rules. This changes the Phase-1 default (`owner`) — a deliberate breaking change so safety is opt-out, not opt-in. Alternative (default read_write) rejected: unsafe for an agent-facing tool.

**2. Single `RailguardValidator.validate(command) -> RailguardResult`, raising `PermissionError`.**
One validator inspects the command type and applies the relevant rules, returning `RailguardResult(allowed, reason)`. Use cases call `validate` first and it raises `PermissionError` on denial, so the deny path is uniform and the use cases stay thin. Alternative (per-use-case inline checks) rejected: scatters policy and invites drift.

**3. Rate limits are windowed counts keyed by action, measured against the injected `Clock`.**
`RateLimits` maps an action (e.g. `forward`) to `max` per window; the validator tracks timestamps of recent operations (in-memory for V1) and denies when the count in the trailing window would exceed `max`. The `Clock` is injected so tests are deterministic. Persistence of the counter across restarts is a non-goal for V1 (documented).

**4. Archive-first is enforced for permanent delete only.**
`DeleteEmailUseCase` soft-deletes (trash) by default. Permanent delete requires `command.permanent=True`, `permanent_delete` not in `BlockedActions`, and — when `ArchiveFirstPolicy` is enabled — the email to be already archived (not in INBOX). The use case checks archived state via the repository/gateway before permanently deleting.

**5. Draft-first sending; new gateway draft methods.**
`CreateDraftUseCase` calls a new `GmailGateway.create_draft(raw_message) -> DraftResult` and returns the `draft_id` for human review; `SendDraftUseCase` calls `send_draft(draft_id)`. `delete_draft(draft_id)` supports discarding. These map to Gmail `users.drafts.{create,send,delete}`. The port and `GmailApiGateway` gain these methods; existing gateway DTO style (plain dataclasses) is followed.

**6. Audit via an event subscriber, not inline logging.**
An `AuditLogHandler` subscribes to the write domain events (`EmailForwarded`, `EmailArchived`, `EmailDeleted`, and draft events) and persists an `AuditLog` entry through `AuditLogRepository`. This decouples auditing from the use cases and guarantees one record per successful write. Correlation id flows from the ambient context (logging correlation id) or is generated per operation.

**7. Events emitted only after the gateway call succeeds.**
Each use case validates → calls the gateway → then publishes its event. A failed gateway call raises before any event, so the audit trail never records a write that did not happen.

## Risks / Trade-offs

- **Breaking default (`owner` → `read_only`)** → Denies writes until configured. Mitigated by a clear CHANGELOG note, `.env.example`, and `configuration.md`; deployments set `read_write` explicitly.
- **In-memory rate-limit counters reset on restart** → Acceptable for V1; a process restart briefly relaxes limits. Documented; a persistent counter is a later option.
- **Archived-state check adds a read before permanent delete** → One extra gateway/repository call; acceptable given permanent delete is rare and destructive.
- **Draft API surface expands the gateway** → New methods added to the port and its single adapter; the fake gateway in tests gains matching methods.

## Migration Plan

Additive except the `access_level` default change. New Alembic migration adds the `audit_log` table (revision after Phase 5's `0001`). Existing deployments must set `AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL=read_write` to retain write capability. No data migration. Railguard framework lands first (`src/Common/Railguards/`, `src/Common/Audit/`), then the write use cases, then the gateway draft methods and adapter, each independently testable with the in-memory event bus and fakes.

## Open Questions

- Should rate-limit state be persisted (survive restart) in V1? Leaning no (in-memory), revisit if abuse is observed.
- Should `AllowedRecipients` support domain wildcards (`@example.com`) in addition to full addresses? Leaning yes — match on exact address or domain suffix.
- Correlation-id source: reuse the logging correlation id vs. generate per use case. Leaning reuse when present, else generate.
