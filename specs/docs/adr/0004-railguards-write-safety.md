# 0004 — Railguards Write-Safety Model

Status: accepted

Context: The server hands mailbox mutation to an autonomous AI agent — forwarding, archiving, deleting, sending. An agent acting on a mistaken instruction, or on a prompt-injection payload embedded in an email, could exfiltrate mail, delete it irrecoverably, or spam contacts. The blast radius of an unconstrained write tool is high and hard to undo. We need write access to be safe by construction, not by trusting the agent or the prompt.

Decision: All writes pass through a **railguards** layer whose master switch is an access level that is **read-only by default**. The controls:

- **Access level** — `read_only` (default) or `read_write`. Under `read_only` no write is possible; a deployment must opt in explicitly.
- **Defense in depth** — when `read_only`, write-category tools are **not registered** with the MCP server at all, so the agent cannot see or call them. When `read_write`, the `RailguardValidator` still checks every command at execution time.
- **Recipient allowlist** — forwarding is limited to configured addresses/domains.
- **Rate limits** — per-action caps within a trailing time window.
- **Archive-first policy** — permanent delete requires the email to be archived first; deletes are soft (Trash) by default.
- **Draft-first sending** — the agent creates a draft; sending is a separate, explicit `send_draft` step for human review.
- **Audit log** — every write is persisted with action, email id, and correlation id.

A denial raises `PermissionError` internally and surfaces to the agent as a structured `permission_denied` error, never an unhandled exception.

Consequences:

- **Easier:** The default deployment cannot mutate a mailbox, so a misconfigured or adversarially-prompted agent is contained. Not registering write tools under `read_only` means their very existence is hidden, shrinking the attack surface. The audit log makes every write reviewable.
- **Harder:** Two enforcement points (registration-time gating and execution-time validation) must stay consistent. Rate-limit state is in-memory and resets on restart. Operators must consciously enable `read_write` and configure the allowlist/limits, which is friction — deliberately so.
- **Future:** New write actions must be added to the railguard action set and covered by the validator, and new controls (e.g. per-recipient quotas, approval callbacks) can be layered into the validator without changing the use cases.
