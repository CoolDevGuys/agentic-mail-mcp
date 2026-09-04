## 1. Structured tool results (no double-encoding)

- [x] 1.1 In `agentic_mail_mcp/MCP/Tools/{read_tools,search_tools,write_tools,intelligence_tools}.py`, change every tool handler return annotation from `-> dict` to `-> dict[str, Any]` (import `Any` from `typing`).
- [x] 1.2 Add a unit test (e.g. `tests/unit/mcp/test_structured_output.py`) asserting every registered tool handler yields non-None `structured_content` (via `func_metadata`) and no `{"result": ...}` wrapping.

## 2. `get_email` field projection

- [x] 2.1 Add `fields: list[str] | None = None` to the `get_email` handler in `read_tools.py`; apply `_normalize_fields` + `_project_email` (same semantics as `search_emails`); mention the option in the tool description.
- [x] 2.2 Tests: `fields=["subject","from","date"]` returns only `id` + requested fields (no body); unknown field maps to `invalid_input`.

## 3. Sender display name on EmailDTO

- [x] 3.1 Add `from_display_name: str | None = None` to `EmailDTO`; in `from_gateway_header` / `from_gateway_message`, split the raw From header with `email.utils.parseaddr`: `from_address` = bare address (raw value kept when `parseaddr` finds no address), `from_display_name` = name part or None.
- [x] 3.2 Add `from_display_name` to `_SEARCH_FIELDS` in `read_tools.py`; document InMail behavior in the `search_emails` description.
- [x] 3.3 Tests in the gmail-application DTO tests: `"Will G. <inmail-hit-reply@linkedin.com>"` → address + name split; bare header → `from_display_name=None`.

## 4. `query_scope` for search

- [x] 4.1 Add `query_scope: str = "all"` to `SearchEmailsQuery` with `__post_init__` validation against `{"all", "subject", "body"}`.
- [x] 4.2 In `build_gmail_query`: scope `subject` → `subject:"<term>"`, scope `body` → `inbody:"<term>"` (skip quoting when the term already contains `"`), `all` → verbatim as today.
- [x] 4.3 Add `query_scope` parameter to the `search_emails` tool, pass it through, document it in the description; `use_cache` path behavior unchanged (scope is only compiled into the Gmail query string).
- [x] 4.4 Tests: `build_gmail_query` for each scope; invalid scope → ValidationError; tool passes scope into the gateway query string.

## 5. Snippet hygiene

- [x] 5.1 In `derive_snippet` (dtos.py): add a module-level `_INVISIBLE_CHARS` frozenset (`U+00AD`, `U+200B`–`U+200F`, `U+2060`–`U+2064`, `U+FEFF`); strip them from both body and fallback; clean + collapse + truncate the fallback too.
- [x] 5.2 Tests: zero-width characters removed; gateway fallback cleaned and truncated like body snippets.

## 6. Gmail-resolvable semantic search

- [x] 6.1 Add `message_id: str | None = None` to `SearchResultDTO`; give `SemanticSearchUseCase` an optional keyword `email_repository` and populate `message_id` via `find_by_id` when wired.
- [x] 6.2 Pass the `email_repo` from `Composition.build_use_cases` into `_build_semantic_search` and the use case; wire `make_env`'s SemanticSearchUseCase in `tests/unit/mcp/conftest.py` the same way.
- [x] 6.3 Update the `semantic_search` tool description to instruct agents to use `message_id` with `get_email`.
- [x] 6.4 Tests: resolvable email → `message_id` populated; unwired/unresolvable → `None`.

## 7. Verification

- [x] 7.1 Run the full unit suite plus lint/typecheck per project guidelines (`Makefile` targets).
