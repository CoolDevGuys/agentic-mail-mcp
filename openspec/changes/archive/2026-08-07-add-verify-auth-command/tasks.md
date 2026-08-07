## 1. Gateway profile lookup

- [x] 1.1 Add `get_profile()` to the `GmailGateway` port returning the account
  email address.
- [x] 1.2 Implement `get_profile()` on `GmailApiGateway` via
  `users().getProfile(userId="me")` (through the existing `_execute` retry path).

## 2. Auth check

- [x] 2.1 Create `agentic_mail_mcp/Bootstrap/auth_check.py` with a
  `check_auth(settings, *, gateway_factory=...) -> AuthCheckResult` that
  sequences: client config → encryption key → token present → live
  `get_profile()`.
- [x] 2.2 Return a structured result (ok flag, stage/status, message, account
  email when known); classify failures as `no_client`, `no_key`, `no_token`,
  `token_rejected` (Google auth error), `unreachable` (other/network), each with
  an actionable message.

## 3. CLI subcommand

- [x] 3.1 Add a `verify-auth` subparser (with the shared `--env-file` option) and
  a `_verify_auth` handler that runs `check_auth`, prints the result (account on
  success), and exits `0` on success / non-zero on failure.
- [x] 3.2 Route `args.command == "verify-auth"` in `main()`.

## 4. HTTP startup preflight

- [x] 4.1 In the `serve` path, when the resolved transport is HTTP, run
  `check_auth` and on failure `logger.warning(...)` with the remediation, then
  continue starting the server. Do not run it for stdio.

## 5. Tests

- [x] 5.1 Unit tests for `check_auth` covering each stage: success (returns
  account), `no_client`, `no_token`, `token_rejected`, `unreachable` — using a
  fake provider/gateway factory (no network).
- [x] 5.2 CLI test: `verify-auth` exits `0` on success and non-zero on failure;
  `--help` lists `verify-auth`.
- [x] 5.3 Startup test: HTTP transport runs the check and logs a warning but
  still starts on failure; stdio transport does not invoke the check.

## 6. Docs

- [x] 6.1 Document `verify-auth` in `README.md` (setup/troubleshooting) and note
  the HTTP-startup warning behavior.
- [x] 6.2 Document `verify-auth` in `specs/docs/configuration.md` as the way to
  confirm the token is valid.

## 7. Verify

- [x] 7.1 Run `ruff`, `mypy`, and the full suite; keep coverage floors green.
- [x] 7.2 Manually run `agentic-mail-mcp verify-auth` against the real account
  (valid token → prints the address; revoked/expired → clear failure).
