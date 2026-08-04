# MCP API Reference

> The Gmail MCP server exposes **tools**, **resources**, and **prompts** over the
> Model Context Protocol. Tools are grouped by category (read, write,
> intelligence, search). Write tools are only registered when
> `railguards.access_level = read_write`; under the default `read_only` they are
> absent from the tool list entirely (see [configuration](configuration.md) and
> the railguards ADR). This document is the source of truth for the MCP surface;
> the README links here rather than restating it.

## Conventions

- **Input schema** — each tool declares a JSON-Schema `object`. A `*` marks a
  required property; all others are optional with a sensible default.
- **`email_id`** — accepts an internal UUID (resolved from the local cache) or a
  Gmail message id (resolved against the live API).
- **Dates** — `YYYY-MM-DD` strings.
- **Output** — tools return a JSON object (email/thread/label DTOs, digests,
  search results) or a small status object. Errors use the
  [structured error format](#error-responses) instead of raising.

## Read tools

Always registered, regardless of access level.

### `search_emails`
Search the mailbox by full-text query and structured filters. Returns a page of email summaries.

| Property | Type | Required | Notes |
|---|---|---|---|
| `query` | string | | Gmail-style full-text query |
| `from_address` | string | | Sender filter |
| `to_address` | string | | Recipient filter |
| `subject` | string | | Subject filter |
| `date_from` | string | | `YYYY-MM-DD` lower bound |
| `date_to` | string | | `YYYY-MM-DD` upper bound |
| `has_attachment` | boolean | | Only mail with attachments |
| `label` | string | | Label filter |
| `unread_only` | boolean | | Only unread |
| `page` | integer | | 1-based page (default 1) |
| `page_size` | integer | | Page size (default 25) |

**Output:** `{ emails: EmailSummary[], page, page_size, next_page_token, total_estimate }`.

### `get_email`
Fetch a single email with its body.

| Property | Type | Required | Notes |
|---|---|---|---|
| `email_id` | string | ✱ | UUID (cache) or Gmail message id (API) |

**Output:** an `Email` object (id, message_id, thread_id, subject, snippet, from/to, date, is_read, labels, body).

### `get_thread`
Fetch a conversation thread and its ordered email ids.

| Property | Type | Required |
|---|---|---|
| `thread_id` | string | ✱ |

**Output:** a `Thread` object (id, thread_id, subject, snippet, participants, email_ids, last_updated, is_read).

### `list_unread`
List unread emails, optionally filtered by label.

| Property | Type | Required | Notes |
|---|---|---|---|
| `limit` | integer | | Max results (default 25) |
| `label` | string | | Restrict to a label |

**Output:** `{ emails: Email[] }`.

### `list_labels`
List Gmail labels filtered by type.

| Property | Type | Required | Notes |
|---|---|---|---|
| `label_type` | string | | `system`, `user`, or `all` (default `all`) |

**Output:** `{ labels: Label[] }`.

## Write tools

Registered **only** when `railguards.access_level = read_write`. Every call is
validated by the `RailguardValidator`; a denial returns a structured
`permission_denied` error (it does not raise).

### `forward_email`
Forward an email to a recipient (subject to the railguard allowlist and rate limits). The original is attached.

| Property | Type | Required | Notes |
|---|---|---|---|
| `email_id` | string | ✱ | |
| `to` | string | ✱ | Must satisfy the recipient allowlist |
| `subject` | string | | |
| `body` | string | | |
| `include_original` | boolean | | Attach the original (default true) |

**Output:** `{ message_id, thread_id }`.

### `archive_email`
Archive an email or a whole thread (removes it from the inbox). Provide `email_id` **or** `thread_id`.

| Property | Type | Required |
|---|---|---|
| `email_id` | string | |
| `thread_id` | string | |

**Output:** `{ status: "archived" }`.

### `delete_email`
Delete an email. Soft-deletes to Trash by default; permanent deletion is only honored when the railguards allow it (action not blocked, archive-first satisfied).

| Property | Type | Required | Notes |
|---|---|---|---|
| `email_id` | string | ✱ | |
| `permanent` | boolean | | Permanent delete (default false) |

**Output:** `{ status: "deleted", permanent: boolean }`.

### `create_draft`
Create a draft for human review without sending it. Returns the draft id to send later with `send_draft`.

| Property | Type | Required |
|---|---|---|
| `to` | string | ✱ |
| `subject` | string | |
| `body` | string | |

**Output:** `{ draft_id }`.

### `send_draft`
Send a previously created, human-reviewed draft.

| Property | Type | Required |
|---|---|---|
| `draft_id` | string | ✱ |

**Output:** `{ message_id, thread_id }`.

### `add_label`
Add a label to an email.

| Property | Type | Required |
|---|---|---|
| `email_id` | string | ✱ |
| `label` | string | ✱ |

**Output:** `{ status: "labeled", label }`.

## Intelligence tools

LLM-backed; always registered.

| Tool | Required params | Optional params | Output |
|---|---|---|---|
| `summarize_email` | `email_id` | | `Summary` (summary_text, model_used) |
| `classify_email` | `email_id` | | `Classification` (category, priority, confidence) |
| `suggest_reply` | `email_id` | | `Suggestion` (draft_text, suggestion_type) |
| `extract_action_items` | `email_id` | | `{ action_items: ActionItem[] }` |
| `daily_digest` | | `date` (`YYYY-MM-DD`, defaults to today) | `Digest` (digest_type, digest_period, email_count, summary_text, items) |
| `weekly_digest` | | `week_start` (any `YYYY-MM-DD` in the target week, defaults to this week) | `Digest` |

Categories for `classify_email` are `urgent`, `normal`, `spam`, `promo`;
priority is `1`–`5`.

## Search tools

### `semantic_search`
Search emails by meaning using natural language. Returns matches ranked by similarity score.

| Property | Type | Required | Notes |
|---|---|---|---|
| `query` | string | ✱ | Natural-language query |
| `limit` | integer | | Max results (default 10) |
| `min_score` | number | | Minimum similarity (default 0.0) |

**Output:** `{ results: SearchResult[] }` where each result has `document_id`, `email_id`, `score`, `metadata`.

## Resources

Read-only projections of server state.

| URI | Name | Returns |
|---|---|---|
| `gmail://account` | account-info | `{ email, access_level }` |
| `gmail://watch` | watch-status | `{ active, history_id }` |
| `search://index` | index-status | `{ document_count }` |

## Prompts

Pre-built prompts that guide an agent to use the server effectively.

| Name | Arguments | Purpose |
|---|---|---|
| `search_strategy` | `goal` | How to search the mailbox effectively for a goal |
| `email_management` | — | A workflow for triaging and managing the inbox |

## Error responses

A tool maps known failures to a structured error object rather than raising, so
the agent-facing surface stays predictable:

```json
{ "error": { "type": "permission_denied", "message": "recipient 'x@evil.com' is not allowed" } }
```

| `type` | Meaning |
|---|---|
| `permission_denied` | A railguard denied the write (read-only access, recipient not allowed, rate limit, blocked action, archive-first). |
| `not_found` | The referenced email/thread does not exist. |
| `invalid_input` | An argument failed validation or parsing (bad id, malformed date, invalid pagination). |
| `internal_error` | An unexpected failure not covered above. |
