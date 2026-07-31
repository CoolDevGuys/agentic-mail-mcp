# Security Guidelines

> Load when touching authentication, authorization, input handling, secrets, file handling, or data exposure.

## Input & output
- Validate/parse **all** external input at the boundary (HTTP body, headers, query, files, webhooks, message payloads). Allowlist over blocklist.
- Parameterized queries only; never interpolate values into SQL, shell commands, or eval-like constructs.
- Encode output for its context: HTML-escape templates, JSON-encode APIs. Frontend: never `innerHTML` untrusted data; use a strict Content-Security-Policy.
- File uploads: validate type by content (not extension), cap size, store outside the web root with generated names.

## Authentication & authorization
- Passwords hashed with a modern KDF (argon2id or bcrypt with strong cost). Never store or log plaintext credentials.
- Sessions/tokens: short-lived access tokens, rotating refresh tokens, revocation path. Cookies: `HttpOnly; Secure; SameSite`.
- Authorize on **every** request at the use-case level (not just UI hiding). Check object ownership, not just role (prevent IDOR).
- Rate-limit auth endpoints; constant-time comparison for secrets.

## Secrets & configuration
- Secrets only from env/secret manager. Never in code, git, logs, error messages, or client bundles.
- Distinct credentials per environment; least-privilege DB users (the app user cannot `DROP`).
- Dependency hygiene: lockfiles committed; automated vulnerability scanning in CI; pin and review before upgrading.

## Data
- Log events, not payloads containing PII/credentials. Redact by default.
- Encrypt sensitive data at rest where warranted; TLS everywhere in transit.
- API responses expose explicit DTO fields only — never serialize entities directly (mass-exposure).
- Errors to clients are generic; details go to server logs with a correlation ID.

## Frontend specifics
- Store tokens in memory or `HttpOnly` cookies — not `localStorage` when avoidable.
- CSRF protection for cookie-authenticated state-changing requests.
- Sanitize/validate anything placed into URLs, `href`, or dynamic imports.
