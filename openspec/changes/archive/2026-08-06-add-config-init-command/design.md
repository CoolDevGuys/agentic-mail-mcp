## Context

The CLI (`agentic_mail_mcp/Bootstrap/cli.py`) exposes `serve` and `auth`
subcommands and reads configuration through `Settings.from_env()`
(`agentic_mail_mcp/Bootstrap/Settings.py`), which loads env vars / `.env` with
the `AGENTIC_MAIL_MCP_` prefix. First-run configuration today is manual: copy
`.env.example` (30 keys) and edit by hand, including hand-writing the Fernet
token encryption key and JSON-formatting list/dict fields. This change adds an
interactive `init` command that produces a valid `.env` in one guided pass.

The wizard must be **testable without a TTY**, must never emit an invalid file,
and must never clobber an existing `.env` silently.

## Goals / Non-Goals

**Goals:**
- One command that walks a user through every section and writes a loadable
  `.env`.
- Auto-generate the encryption key so no secret is hand-written.
- Validate inputs with the same constraints as `Settings`, re-prompting on error.
- Preserve any existing `.env` via a timestamped backup before overwrite.
- Keep the wizard logic pure and unit-testable (injected input/output streams).

**Non-Goals:**
- No change to `Settings` fields, the env-var contract, or `.env.example` as the
  canonical reference.
- Not a secrets manager — values are written in plaintext to `.env` exactly as
  today's manual flow does.
- Does not run `auth` or start the server; it only writes configuration and
  points to the next step.
- Not a flags-only/non-interactive generator (explicitly deferred; the chosen
  scope is the full guided walkthrough).

## Decisions

**1. New module `Bootstrap/config_init.py`, driven by injected I/O.**
The wizard is a function operating over an input callable and an output stream
(e.g. `run_init(prompt=input, out=sys.stdout, env_path=Path(".env"))`), not
direct `input()`/`print()` calls scattered in `cli.py`. Rationale: tests script
a sequence of answers (including invalid-then-valid) and assert on the written
file without a real terminal. `cli.py` stays a thin adapter: an `init` subparser
that calls the module. Alternative (inline in `cli.py`) rejected — untestable and
mixes concerns.

**2. A declarative field table drives the prompts.**
Each field is a small record: env key, human label, default, and a validator/
parser. The walkthrough iterates the table in `.env.example` order so the output
matches the documented reference and stays easy to keep in sync. Rationale:
avoids 30 bespoke prompt blocks; adding a field later is one row. Alternative
(introspecting the pydantic `Settings` model) rejected for v1 — more coupling and
reflection complexity than the fixed, documented key set warrants.

**3. Validation reuses the settings constraints, per field.**
Constrained fields validate inline (access level ∈ {read_only, read_write};
transport ∈ {stdio, http}; ints for port/TTL/embedding dimension; bools for
flags; a credentials-file path that exists when provided). On invalid input the
wizard prints the reason and re-prompts the same field. As a final safety net,
after assembly the wizard loads the result through `Settings` to guarantee a
loadable file. Rationale: fail at the prompt (good UX) and fail-closed at the end
(never write garbage).

**4. Encryption key: generate when empty.**
The key prompt is optional; empty input triggers generation of a high-entropy
value (`secrets.token_urlsafe`, consistent with the docs). Any typed value is
kept verbatim. Rationale: removes the single most error-prone manual step while
still letting a user paste a shared key (needed for the headless token-copy
flow).

**5. Existing-file safety: confirm + timestamped backup.**
If `.env` exists, the wizard asks to overwrite; declining aborts with no changes.
Confirming copies the current file to `.env.bak-<UTC-timestamp>` before writing.
Rationale: mirrors the safe pattern already used elsewhere in this repo and
prevents accidental loss of a working (possibly secret-bearing) config.

**6. Serialization matches the loader.**
List/dict fields (allowed recipients, blocked actions, rate limits, scopes) are
written as JSON via `json.dumps`; bools as lowercase `true`/`false`; the file is
written `0600` where the OS supports it, since it may hold secrets. Rationale:
the values must round-trip through `Settings.from_env()`.

## Risks / Trade-offs

- **[Drift between the wizard's field table and `.env.example`/`Settings`]** →
  A unit test asserts the generated `.env` loads via `Settings.from_env()` and
  that every `AGENTIC_MAIL_MCP_` key in `.env.example` is produced, so an added
  setting that the wizard forgets is caught in CI.
- **[Plaintext secrets on disk]** → Same exposure as the existing manual `.env`;
  mitigated by `0600` permissions and by generating (not echoing) the key. Not a
  regression.
- **[Non-TTY / piped input hitting EOF mid-wizard]** → The prompt helper treats
  EOF as "abort without writing", so a truncated non-interactive run fails closed
  rather than writing a partial file.
- **[Localization / unexpected input]** → Kept minimal: trimmed strings, explicit
  yes/no parsing, numeric coercion with re-prompt.

## Migration Plan

Purely additive — a new subcommand and module; no changes to existing commands,
settings, or persisted data. Rollback is removing the subcommand. Docs
(`README.md`, `specs/docs/configuration.md`) are updated to present `init` as the
recommended first step while the manual `.env.example` path remains valid.

## Open Questions

- None blocking. (A future `--non-interactive`/flags mode is out of scope here
  and can be added later without changing this design.)
