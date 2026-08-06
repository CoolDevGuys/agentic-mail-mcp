## 1. Wizard module

- [x] 1.1 Create `agentic_mail_mcp/Bootstrap/config_init.py` with a testable
  `run_init(*, prompt, out, env_path)` entry point (injected input callable and
  output stream; no bare `input()`/`print()`).
- [x] 1.2 Define the declarative field table (env key, label, default, parser/
  validator) covering every section in `.env.example` order: gmail, database,
  railguards, mcp, llm, search, notifications, logging.
- [x] 1.3 Implement the prompt helper: show label + default, Enter keeps default,
  trim input, treat EOF as safe abort (no file written).
- [x] 1.4 Implement per-field validation with re-prompt for constrained fields
  (access level, transport, ints for port/TTL/embedding dimension, bools) and an
  existing-path check for the credentials file when provided.
- [x] 1.5 Auto-generate `AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY` (via
  `secrets.token_urlsafe`) when the prompt is left empty; keep a typed value
  verbatim.
- [x] 1.6 Serialize values for the loader: JSON for list/dict fields, lowercase
  bools; assemble the `.env` content.
- [x] 1.7 Implement existing-`.env` handling: confirm overwrite, write
  `.env.bak-<UTC-timestamp>` before overwriting, abort with no changes on
  decline.
- [x] 1.8 Write the file (`0600` where supported) and, as a final safety net,
  load it through `Settings` to guarantee it is valid; print the path and next
  steps (`auth`, then start the server).

## 2. CLI integration

- [x] 2.1 Add an `init` subparser to `agentic_mail_mcp/Bootstrap/cli.py` and a
  thin `_init` handler that calls `run_init`.
- [x] 2.2 Route `args.command == "init"` in `main()`; ensure `--help` lists
  `init` next to `serve`/`auth`.
- [x] 2.3 Change the no-subcommand branch to print help and exit (do NOT call
  `_serve`); drop the "(default)" note from the `serve` subparser help.
- [x] 2.4 Update the breaking call sites to start the server explicitly with
  `serve`: `Dockerfile` `CMD` → `["agentic-mail-mcp", "serve"]`; README MCP
  client config (`args`/`command`) and the HTTP run command → include `serve`.

## 3. Tests

- [x] 3.1 Test: accepting all defaults writes a `.env` that loads via
  `Settings.from_env()` and contains every `AGENTIC_MAIL_MCP_` key present in
  `.env.example` (drift guard).
- [x] 3.2 Test: empty key prompt generates a high-entropy key; a typed key is
  preserved verbatim.
- [x] 3.3 Test: invalid-then-valid input for a constrained field (access level /
  transport / port) re-prompts and ultimately writes the valid value.
- [x] 3.4 Test: existing `.env` → confirming overwrite creates a timestamped
  backup; declining leaves the original untouched.
- [x] 3.5 Test: list/dict fields are emitted as valid JSON that round-trips
  through `Settings`.
- [x] 3.6 Test: invoking the CLI with no subcommand prints help and does not
  start the server (and `--help` lists `serve`/`auth`/`init`).

## 4. Docs

- [x] 4.1 Update `README.md` Quick start to present `agentic-mail-mcp init` as the
  recommended first step (before `auth`).
- [x] 4.2 Update `specs/docs/configuration.md` with an `init` walkthrough section
  and note `.env.example` remains the reference of record.

## 5. Verify

- [x] 5.1 Run `ruff check`, `mypy`, and the full test suite; keep the Domain
  (≥90%) and overall (≥80%) coverage floors green.
- [x] 5.2 Manually run `agentic-mail-mcp init` in a scratch dir and confirm the
  generated `.env` loads and `serve`/`auth` accept it.
