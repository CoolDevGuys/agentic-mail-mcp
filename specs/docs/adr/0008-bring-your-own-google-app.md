# 0008 — Bring-Your-Own Google App (No Central App, No Verification)

Status: accepted

Context: To talk to Gmail the server needs a Google OAuth client and a per-user refresh token. Two distribution models are possible. (a) **Central app:** the project publishes and verifies a single Google Cloud app that all users authorize against. (b) **Bring-your-own (BYO):** each user creates their own OAuth client in their own Google Cloud project and authorizes their own mailbox. Gmail's `gmail.modify` is a *restricted* scope: a central app used by external users must pass Google's OAuth verification and a CASA security assessment — a weeks-long, ongoing obligation — and it makes the project operator a processor of every user's mailbox access.

Decision: **Distribute as a local, bring-your-own-credentials tool.** There is no central Google app. Each user:

1. Creates their own Google Cloud project and Desktop-app OAuth client, and downloads its `credentials.json`.
2. Points the server at it (`AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE`, or `client_id`/`client_secret`).
3. Runs `agentic-mail-mcp auth` once to grant their own account access; the encrypted token is stored locally.

Because each app only ever authorizes its own owner (as a test user, or in an unverified production app), **Google's verification requirement does not apply**. Credentials and tokens never leave the user's machine; the project ships no service that touches anyone's mail.

Consequences:

- **Easier:** No app-verification or security-assessment burden for the project; no central service to run, secure, or trust; each user's data and credentials stay entirely on their machine; the project can be published as a plain package/image.
- **Harder:** Each user does a one-time ~5-minute Google Cloud setup (documented in `configuration.md`). Apps left in "Testing" status expire refresh tokens after 7 days; users avoid this by publishing their own (still unverified) app to production, which needs no Google review for single-user use.
- **Future:** A hosted, multi-tenant offering — if ever desired — would be a *different* product with per-user OAuth, isolated token storage, and the full Google verification path; it is explicitly out of scope here.
