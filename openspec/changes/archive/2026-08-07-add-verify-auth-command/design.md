## Context

The pieces already exist to build an auth check: `resolve_client_config`
(Composition) tells whether a Google client is configured; `build_oauth_provider`
gives `has_token()` / `load_credentials()`; `GmailApiGateway.from_credentials`
builds an authenticated service. What's missing is a single function that
sequences these into a clear pass/fail with an account identity, plus wiring it
to a `verify-auth` command and to HTTP startup.

The user chose **warn-and-continue** at HTTP startup and the name **`verify-auth`**.

## Goals / Non-Goals

**Goals:**
- One reusable check that validates config → key → token → a **live** Gmail call.
- A `verify-auth` subcommand (exit 0 on success, non-zero on failure) with
  actionable, stage-specific messages.
- HTTP startup runs the check and **warns but continues** on failure.
- stdio startup does **not** run the network check.
- Keep it testable without real Google credentials.

**Non-Goals:**
- Not a full health endpoint (DB, LLM, search) — auth only. The name leaves room
  to grow, but scope here is the Gmail token/credentials.
- Does not attempt to re-authorize or refresh interactively; it reports and
  points at `auth`.
- Does not change stdio behavior beyond leaving startup untouched.

## Decisions

**1. A pure check returning a structured result, not prints.**
`check_auth(settings) -> AuthCheckResult` (ok flag, a stage/status, a message,
and the account email when known). The CLI formats and sets the exit code; the
server logs a warning. Rationale: one code path serves both the command and the
startup hook and is unit-testable by asserting on the result. Alternative
(printing inside the check) rejected — couples it to a caller.

**2. Reuse composition helpers; inject the gateway factory for tests.**
The check calls `resolve_client_config`, `build_oauth_provider`, then builds the
gateway from `load_credentials()` and calls a new `get_profile()`. The gateway
factory is injectable so tests pass a fake that returns an email or raises,
covering success, missing-token, and rejected-token without network. Rationale:
mirrors the existing composition seams used elsewhere.

**3. Add `get_profile()` to the gateway/port rather than reaching into
`_service`.** It returns the account email via `users().getProfile`. Rationale:
the live write test already pokes `_service.users().getProfile`; promoting it to
a method keeps the check clean and gives one tested call site. It is a
lightweight, read-only call suitable as a liveness probe.

**4. Classify failures by stage for actionable messages.**
Stages: `no_client` → configure `CLIENT_SECRETS_FILE` or id/secret; `no_key` →
set `TOKEN_ENCRYPTION_KEY`; `no_token` → run `auth`; `token_rejected` (a Gmail
auth error, e.g. `invalid_grant`) → token expired/revoked, re-run `auth`;
`unreachable` (network) → transient, retry. Rationale: the message must tell the
operator exactly what to do.

**5. HTTP-only startup hook, warn-and-continue.**
In the `serve` path, after building use cases and before/along with running the
server, if the resolved transport is HTTP run the check and, on failure,
`logger.warning(...)` with the remediation; never raise. stdio skips it.
Rationale: matches the chosen policy and avoids slowing stdio client launch or
crash-looping supervised HTTP deployments.

## Risks / Trade-offs

- **[A live call at every HTTP start adds a small startup delay / API call]** →
  One lightweight `getProfile` per start; acceptable and bounded. Warn-and-
  continue means a transient network blip never blocks startup.
- **[Distinguishing "expired/revoked" from "network down"]** → Map Google auth
  errors (`RefreshError` / `invalid_grant`, 401) to `token_rejected` and other
  exceptions to `unreachable`, so the message doesn't cry "revoked" on a blip.
- **[Warn-and-continue could be missed in noisy logs]** → Make the warning
  prominent and single-line-greppable (clear prefix), and the on-demand
  `verify-auth` remains the authoritative, exit-coded check for scripts.

## Migration Plan

Purely additive: a new subcommand, a new check module, a new gateway method, and
a startup log line for HTTP. No behavior change for existing commands or stdio.
Rollback is removing the subcommand and the startup call.

## Open Questions

None blocking.
