## Context

Agent testing of the MCP server on real job-application mail surfaced six
ergonomic flaws. Ground truth from the current code:

- **Double encoding**: every handler in `MCP/Tools/*.py` is annotated
  `-> dict`. Verified against the installed `mcp==2.0.0`: a bare `dict` return
  annotation produces **no** `structuredContent` on `CallToolResult` — clients
  get only the JSON text block (and some wrap it as `{"result": "<string>"}`),
  so agents parse twice. `dict[str, Any]` produces an **unwrapped** structured
  object (`wrap_output=False`, RootModel path). The `_safe_handler` wrapper in
  `Server.py` copies the handler signature, so the change propagates.
- **`get_email`**: no `fields` parameter, although `read_tools.py` already has
  `_normalize_fields` / `_project_email` used by `search_emails`.
- **InMail sender**: `GmailMessage.from_`/`GmailMessageHeader.from_` hold the
  raw header (`"Will G. <inmail-hit-reply@linkedin.com>"`) and flow verbatim
  into `EmailDTO.from_address` on gateway paths, while the entity path stores a
  bare `EmailAddress` — inconsistent, and the display name is lost everywhere
  except by string-parsing `from_address`.
- **Query looseness**: `build_gmail_query` appends `query_string` verbatim to
  the Gmail query (full-text over everything). Gmail supports `subject:"…"` and
  `inbody:"…"` operators.
- **Snippets**: `derive_snippet` collapses whitespace and truncates body-derived
  snippets, but returns the gateway-provided fallback **verbatim** (Gmail
  snippets from LinkedIn contain zero-width characters `U+200B`-family), and
  never strips invisible characters from either source.
- **Opaque ids**: `search_emails`/`get_email` already use the Gmail message id
  as `id` (`EmailDTO.from_entity` sets `id=email.message_id.value`); the
  remaining offender is `semantic_search`, whose `SearchResultDTO.email_id` is
  the internal UUID with no way to map it to a Gmail message id.

## Goals / Non-Goals

**Goals:**
- Every tool returns real structured content (no double-parse).
- `get_email(fields=…)` for partial fetches.
- Sender display names visible on live-path DTOs without header parsing.
- `query_scope` to restrict full-text to subject or body.
- Snippets clean of invisible characters with consistent truncation.
- Semantic-search results carry the Gmail `message_id` when resolvable.

**Non-Goals:**
- No database/migration changes (display names are not persisted; the entity
  path yields `from_display_name=None`).
- No change to the meaning of `id` in email DTOs (already the Gmail message id).
- No To-header display-name handling (only From).

## Decisions

### 1. Structured output: `-> dict` → `-> dict[str, Any]`
All tool handlers in `read_tools.py`, `search_tools.py`, `write_tools.py`,
`intelligence_tools.py`. Verified empirically: `dict[str, Any]` hits the SDK's
`_create_dict_model` RootModel path (no `{"result": …}` wrapping). Cheaper and
more robust than declaring a Pydantic model per tool.

### 2. `get_email` field projection
Add `fields: list[str] | None = None` to the `get_email` handler and reuse
`_normalize_fields` + `_project_email` unchanged (both are EmailDTO-generic).
Unknown field → `ValidationError` → `invalid_input`, matching `search_emails`.

### 3. `from_display_name` on `EmailDTO`
- New field `from_display_name: str | None = None` (last field with default —
  no call-site churn).
- `from_gateway_header` / `from_gateway_message`: split the raw header with
  `email.utils.parseaddr`; `from_address` becomes the bare address (matching
  the entity path), `from_display_name` the name part (None when empty). If
  `parseaddr` yields no address (malformed), keep the raw value as
  `from_address` so no information is lost.
- `from_entity`: display name is not stored on the aggregate → `None`. Not
  persisting it (would need a migration) is acceptable: search defaults to the
  live gateway.
- `_SEARCH_FIELDS` in `read_tools.py` gains `from_display_name`.

### 4. `query_scope`
- `SearchEmailsQuery.query_scope: str = "all"`, validated in `__post_init__`
  against `{"all", "subject", "body"}`.
- `build_gmail_query`: `all` → append verbatim (current); `subject` →
  `subject:"<q>"`; `body` → `inbody:"<q>"` — quoting the value (Gmail requires
  quotes for multi-word values; a term containing `"` is passed unquoted rather
  than corrupted).
- Tool gains `query_scope: str = "all"`; the description documents the
  company-name-noise use case.

### 5. Snippet hygiene in `derive_snippet`
- Module-level `_INVISIBLE_CHARS` frozenset: `U+00AD`, `U+200B`–`U+200F`,
  `U+2060`–`U+2064`, `U+FEFF` (zero-width, bidi controls, word-joiners, soft
  hyphen, BOM).
- Both the body text **and** the gateway fallback are cleaned: strip invisible
  chars → collapse whitespace → truncate at `max_length` with `…`. The fallback
  path no longer returns Gmail's verbatim snippet.

### 6. Gmail-resolvable semantic search
- `SearchResultDTO` gains `message_id: str | None = None`.
- `SemanticSearchUseCase.__init__` gains optional `email_repository` (keyword,
  default `None` → `message_id` stays `None`, fully backwards-compatible for
  non-`search`-extra wiring).
- `execute`: when the repository is wired, resolve each `SearchResult.email_id`
  (UUID) via `find_by_id` and populate `message_id` from the entity's
  `message_id.value`.
- `Composition._build_semantic_search(settings, email_repo)` receives the
  repository already built in `build_use_cases` and passes it through.
- Tool description tells the agent to pass `message_id` to `get_email`
  (`email_id` remains the internal UUID fallback).

## Risks / Trade-offs

- **`from_address` value change (raw header → bare address) on live paths**:
  strictly more precise; existing tests use bare addresses and keep passing. An
  agent that previously regex'd `from_address` now gets a cleaner value plus an
  explicit name field.
- **`query_scope` quoting**: `subject:`/`inbody:` are Gmail search semantics
  (substring on the tokenized field), not exact match — same engine, narrower
  field; the user's noise problem is solved without inventing a scorer.
- **Semantic results for uncached emails**: `message_id=None` (documented in
  the description) — indexing without the email repository has no way to know
  the Gmail id; a rebuild after indexing covers it.

## Migration Plan

Purely additive parameters with current-behavior defaults; no config, schema,
or migration changes. Old clients keep working (they can ignore
structuredContent); new clients get real objects.

## Open Questions

None blocking.
