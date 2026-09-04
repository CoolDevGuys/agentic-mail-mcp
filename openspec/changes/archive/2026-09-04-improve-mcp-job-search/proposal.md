# Improve agent-facing ergonomics of the email tools

## Why

Real-world use of the MCP server to triage job-application mail surfaced six
ergonomic flaws in the agent-facing surface. Each one costs the calling agent
extra parsing, extra calls, or outright wrong results:

1. **Double-encoded results.** Tool handlers are annotated `-> dict`, which the
   MCP SDK cannot derive a structured-output schema from, so clients receive a
   JSON string (sometimes re-wrapped as `{"result": "..."}`) that must be
   parsed a second time.
2. **`get_email` has no field selector.** Unlike `search_emails`, it always
   returns the full body (7–9 KB per forwarded email) even when only
   subject/from/date are needed.
3. **LinkedIn InMail sender is a generic alias** (`inmail-hit-reply@linkedin.com`)
   with the real person only in the display name; the DTO exposes no display
   name, so "who sent this" requires parsing the raw header.
4. **Full-text `query` is too loose.** Searching a company name (e.g. "Luma")
   matches CI/build notifications containing the term (`luma-coding-challenge`)
   because there is no way to restrict the query to subject or body.
5. **Snippets carry zero-width spaces** (LinkedIn inserts `U+200B`-family
   characters) and the gateway-provided fallback snippet is neither cleaned nor
   truncated consistently.
6. **`semantic_search` returns only the internal UUID** as `email_id`; an agent
   cannot hand it to Gmail-facing tools or correlate it with a Gmail message id
   without an extra lookup, and emails that were never cached cannot be
   resolved at all.

## What Changes

- **Structured output for every tool**: annotate handlers `dict[str, Any]` so
  the SDK emits real structured content (verified against `mcp` 2.0.0:
  `dict[str, Any]` produces unwrapped `structuredContent`; bare `dict`
  produces none).
- **`get_email(fields=[...])`**: reuse the existing `search_emails` field
  projection so a single email can be fetched as subject/from/date only.
- **`from_display_name` on `EmailDTO`**: derive it (and a bare `from_address`)
  from the raw `From` header on the live gateway paths — so InMail senders are
  identifiable without string parsing.
- **`query_scope` for `search_emails`**: `"all"` (default), `"subject"`, or
  `"body"` — compiled to `subject:"…"` / `inbody:"…"` in the Gmail query.
- **Snippet hygiene**: strip zero-width/bidi/soft-hyphen characters and apply
  the same whitespace-collapse + truncation to the fallback snippet as to
  body-derived snippets.
- **Gmail-resolvable semantic results**: `SearchResultDTO` gains
  `message_id` (the Gmail message id of the matched email) when the email
  resolves from the local repository, and the tool description tells the agent
  to use it with `get_email`.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `mcp-server`: tool results must be structured objects; `get_email` accepts
  `fields`; `search_emails` accepts `query_scope`; `semantic_search` results
  carry the Gmail `message_id`.
- `gmail-application`: `EmailDTO` exposes `from_display_name` with a bare
  `from_address`; `SearchEmailsQuery` gains `query_scope`; snippets are
  sanitized and consistently truncated.
- `search-application`: `SemanticSearchUseCase` resolves matched emails to
  their Gmail message ids.

## Impact

- **Code**: `MCP/Tools/{read_tools,search_tools,write_tools,intelligence_tools}.py`
  (annotations, `fields`, `query_scope`), `Gmail/Application/DTO/dtos.py`
  (display name, snippet cleaning), `Gmail/Application/Queries/queries.py` +
  `UseCases/search_emails.py` (`query_scope`),
  `Search/Application/UseCases/{semantic_search,dtos}.py` (`message_id`),
  `Bootstrap/Composition.py` (wire the email repository into semantic search).
- **Tests**: unit tests per behavior (tool projection, scope compilation,
  snippet cleaning, display-name parsing, structured output, semantic
  `message_id`); existing tests updated where `from_address` becomes the bare
  address.
- **No breaking API changes**: all new parameters are optional with the current
  behavior as default; the `id` field keeps its current meaning.
