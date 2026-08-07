## Why

Today the only way to know whether the stored Google token still works is to
run a real tool and see it fail — and a token can be present on disk yet
expired or revoked (Google expires "Testing"-mode refresh tokens after 7 days).
Operators need a way to confirm auth **before** wiring up an agent, and a
long-running HTTP server should surface a broken token at startup instead of on
the first user request.

## What Changes

- Add an `agentic-mail-mcp verify-auth` subcommand that runs a **preflight auth
  check** and reports the result:
  - client config resolvable (secrets file or id/secret) → encryption key set →
    token present → a **live Gmail call** (`getProfile`) proving the refresh
    token is still valid.
  - On success it prints the authorized **account email** and exits `0`; on any
    failure it prints an actionable message (which step failed and how to fix
    it) and exits non-zero.
- Run the **same check at HTTP server startup**, logging a prominent **warning**
  (with the fix) when it fails but **still starting** the server — so a
  supervised deployment does not crash-loop, and tools keep returning their
  usual clear errors until auth is fixed.
- The check is **skipped for stdio startup** (the client launches the process on
  demand and lazy tool errors already cover it; a blocking network call would
  slow client launch).
- Add a small `get_profile()` method to the Gmail gateway (returns the account
  email) so the check doesn't reach into gateway internals.
- `verify-auth` accepts the shared `--env-file` option like the other commands.

## Capabilities

### New Capabilities
- `auth-verification`: An on-demand and startup preflight that validates Google
  credentials and the stored token by round-tripping to Gmail, with actionable
  reporting and a warn-but-continue policy at HTTP startup.

### Modified Capabilities
- `cli`: the no-subcommand help now also lists `verify-auth` among the available
  subcommands.

## Impact

- **Code**: new check function (e.g. `agentic_mail_mcp/Bootstrap/auth_check.py`)
  built from `Settings` via the existing composition helpers
  (`resolve_client_config`, `build_oauth_provider`, the Gmail gateway); a
  `verify-auth` subparser + handler in `cli.py`; an HTTP-startup call in the
  `serve` path (warn-and-continue); a `get_profile()` method on
  `GmailApiGateway` (and its port).
- **Tests**: unit tests for the check (each failure mode + success) with a fake
  gateway/provider; a CLI dispatch test; a test that HTTP startup warns but
  continues while stdio does not run the check.
- **Docs**: `README.md` and `specs/docs/configuration.md` document `verify-auth`
  in the setup/troubleshooting flow.
- **Dependencies**: none new.
