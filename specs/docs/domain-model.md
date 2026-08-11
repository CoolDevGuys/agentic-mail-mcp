# Domain Model

> This document describes the domain models for each bounded context:
> entities, value objects, aggregates, repository ports, gateway ports,
> and domain events.

---

## Gmail Bounded Context

The Gmail context manages email messages, threads, attachments, and labels.
It is the primary bounded context, interacting with the Gmail API through
the `GmailGateway` anti-corruption layer.

### Aggregates

#### Email

Aggregate root representing a single email message.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local unique identifier |
| `message_id` | `GmailMessageId` | Gmail API message ID |
| `thread_id` | `ThreadId` | Gmail thread ID |
| `snippet` | `str` | Short preview text |
| `subject` | `str` | Email subject line |
| `from_address` | `EmailAddress \| None` | Sender address |
| `to_addresses` | `list[EmailAddress]` | Recipient addresses |
| `date_sent` | `datetime \| None` | Send timestamp |
| `is_read` | `bool` | Read status |
| `labels` | `frozenset[str]` | Applied labels (read-only view) |
| `body` | `str` | Email body text |
| `attachments` | `list[str]` | Attachment identifiers |
| `is_trashed` | `bool` | Trash status |

**Behaviors:**

| Method | Description | Domain Events |
|---|---|---|
| `from_gmail_message(...)` | Factory from Gmail API data | — |
| `mark_read()` | Mark as read | — |
| `add_label(label)` | Add label (unique constraint) | `EmailLabeled` |
| `remove_label(label)` | Remove label | — |
| `archive()` | Archive from inbox | `EmailArchived` |
| `move_to_trash()` | Move to trash | `EmailDeleted` |
| `restore_from_trash()` | Restore from trash | — |

**Invariants:**
- Labels are unique (set-based storage)
- Cannot restore an email that is not in trash

#### Thread

Aggregate root representing a conversation thread.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local unique identifier |
| `thread_id` | `ThreadId` | Gmail thread ID |
| `snippet` | `str` | Preview text |
| `subject` | `str` | Thread subject |
| `participants` | `list[str]` | All participants |
| `email_ids` | `tuple[UUIDId, ...]` | Ordered email IDs (read-only) |
| `last_updated` | `datetime` | Last modification time |
| `is_read` | `bool` | Read status |

**Behaviors:**

| Method | Description |
|---|---|
| `create(thread_id, email_ids, ...)` | Factory (requires at least one email) |
| `add_email(email_id)` | Add email to thread (deduplicates) |
| `mark_read()` | Mark entire thread as read |

**Invariants:**
- Thread must contain at least one email
- Email IDs are not duplicated

#### Attachment

Entity representing an email attachment.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local unique identifier |
| `file_name` | `str` | Original file name |
| `mime_type` | `str` | MIME type |
| `size_bytes` | `int` | File size in bytes |
| `attachment_id` | `str` | Gmail attachment ID |
| `download_url` | `str` | Download URL |

#### Label

Entity representing a Gmail label.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local unique identifier |
| `label_id` | `str` | Gmail label ID |
| `name` | `str` | Label display name |
| `color` | `str` | Label color |
| `type` | `str` | `"system"` or `"user"` |

**Behaviors:**

| Method | Description |
|---|---|
| `rename(new_name)` | Rename label (user labels only) |

**Invariants:**
- System labels cannot be renamed

**System labels:** INBOX, SPAM, TRASH, SENT, DRAFT, IMPORTANT, STARRED, UNREAD, CATEGORY_PERSONAL, CATEGORY_PROMOTIONS, CATEGORY_UPDATES, CATEGORY_FORUMS

### Value Objects

#### EmailAddress

Validated email address (RFC 5322 subset).

| Field | Type | Description |
|---|---|---|
| `value` | `str` | Raw email string |
| `local_part` | `str` | Part before `@` (property) |
| `domain` | `str` | Part after `@` (property) |

**Validation:** Non-empty, regex format check, max 254 characters.

#### GmailMessageId

Wraps a Gmail message ID string. Non-empty validation.

#### ThreadId

Wraps a Gmail thread ID string. Non-empty validation.

#### HistoryId

Wraps a Gmail history ID string (monotonically increasing). Non-empty validation.

#### GmailQuery

Wraps a Gmail search query string with builder classmethods.

| Builder | Output |
|---|---|
| `from_sender(sender)` | `from:{sender}` |
| `with_subject(subject)` | `subject:{subject}` |
| `date_range(after, before)` | `after:YYYY/MM/DD before:YYYY/MM/DD` |
| `has_attachment()` | `has:attachment` |
| `with_label(label)` | `{label}` |
| `unread()` | `is:unread` |
| `query.and_(other)` | `{query} {other}` |

**Validation:** Non-empty, max 500 characters.

### Repository Ports

#### EmailRepository

| Method | Returns | Description |
|---|---|---|
| `find_by_id(id)` | `Email \| None` | Find by local UUID |
| `find_by_gmail_message_id(message_id)` | `Email \| None` | Find by Gmail message ID |
| `find_by_thread_id(thread_id)` | `list[Email]` | Find all emails in thread |
| `search(query)` | `list[Email]` | Search by Gmail query string |
| `list_unread(limit)` | `list[Email]` | List unread emails |
| `save(email)` | `None` | Persist email |
| `delete(id)` | `None` | Remove email |

#### ThreadRepository

| Method | Returns | Description |
|---|---|---|
| `find_by_id(id)` | `Thread \| None` | Find by local UUID |
| `find_by_gmail_thread_id(thread_id)` | `Thread \| None` | Find by Gmail thread ID |
| `save(thread)` | `None` | Persist thread |
| `delete(id)` | `None` | Remove thread |

> No production code path calls `save()` on this port, so it is never
> populated. `GetThreadUseCase` resolves threads live from `GmailGateway`
> (`get_thread`) instead of this repository — see
> [ADR 0007](adr/0007-persistence-read-through-cache.md).

### Gateway Port

#### GmailGateway

Anti-corruption layer port isolating the domain from the Gmail API.

| Method | Returns | Description |
|---|---|---|
| `list_messages(query, page_token, max_results)` | `GmailListResponse` | List messages with pagination |
| `get_message(message_id, fmt)` | `GmailMessage` | Get full message |
| `get_batch_messages(message_ids)` | `list[GmailMessage]` | Get multiple messages |
| `get_thread(thread_id)` | `GmailThread \| None` | Get a full thread (`users.threads.get`), every message with its body |
| `send_message(raw_message)` | `SentMessageResult` | Send raw message |
| `modify_message(message_id, add_labels, remove_labels)` | `ModifyResult` | Modify labels |
| `trash_message(message_id)` | `None` | Move to trash |
| `untrash_message(message_id)` | `None` | Restore from trash |
| `delete_message(message_id)` | `None` | Permanently delete |
| `list_labels()` | `list[GmailLabel]` | List all labels |
| `watch(notification_url, webhook_token)` | `WatchResponse` | Start push notifications |
| `stop_watch()` | `StopWatchResult` | Stop push notifications |
| `get_history(history_id, start_history_id)` | `GmailHistory` | Get history changes |
| `download_attachment(message_id, attachment_id)` | `bytes` | Download attachment |

### Mappers

- **EmailMapper.to_domain(gateway_message)** - Converts `GmailMessage` to `Email` aggregate
- **ThreadMapper.to_domain(gateway_data)** - Converts gateway data to `Thread` aggregate

### Domain Events

| Event | Fields | Raised By |
|---|---|---|
| `EmailReceived` | `email_id`, `from_address`, `subject`, `received_at` | External sync |
| `EmailArchived` | `email_id`, `archived_at` | `Email.archive()` |
| `EmailDeleted` | `email_id`, `deleted_at` | `Email.move_to_trash()` |
| `EmailForwarded` | `email_id`, `forwarded_to`, `forwarded_at` | Forward use case |
| `EmailLabeled` | `email_id`, `label_name`, `labeled_at` | `Email.add_label()` |
| `InboxSynchronized` | `history_id`, `synchronized_at`, `email_count` | History sync |

---

## Intelligence Bounded Context

The Intelligence context provides AI-powered email analysis: summarization,
classification, reply suggestions, and digest generation.

### Entities

#### Summary

AI-generated email summary.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local identifier |
| `email_id` | `UUIDId` | Referenced email |
| `summary_text` | `str` | Generated summary |
| `model_used` | `str` | LLM model identifier |
| `created_at` | `datetime` | Creation timestamp |

**Validation:** `summary_text` must not be empty.

#### Classification

AI-generated email classification.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local identifier |
| `email_id` | `UUIDId` | Referenced email |
| `category` | `str` | One of: `urgent`, `normal`, `spam`, `promo` |
| `priority` | `int` | 1 (lowest) to 5 (highest) |
| `confidence` | `float` | 0.0 to 1.0 |
| `model_used` | `str` | LLM model identifier |
| `created_at` | `datetime` | Creation timestamp |

**Validation:** Category in allowed set, priority 1-5, confidence 0.0-1.0.

#### Suggestion

AI-generated action suggestion.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local identifier |
| `email_id` | `UUIDId` | Referenced email |
| `suggestion_type` | `str` | One of: `reply`, `forward`, `ignore` |
| `draft_text` | `str \| None` | Generated draft text |
| `model_used` | `str` | LLM model identifier |
| `created_at` | `datetime` | Creation timestamp |

**Validation:** `suggestion_type` in allowed set.

### Value Objects

#### PromptTemplate

Parameterized prompt template with variable substitution.

| Field | Type | Description |
|---|---|---|
| `name` | `str` | Template identifier |
| `template` | `str` | Template string with `{variable}` placeholders |

**Methods:** `render(**kwargs) -> str` - Substitutes variables, raises `ValidationError` if required variables are missing.

#### ModelConfig

LLM model configuration.

| Field | Type | Description |
|---|---|---|
| `provider` | `str` | LLM provider name |
| `model_id` | `str` | Model identifier |
| `max_tokens` | `int` | Maximum output tokens |
| `temperature` | `float` | Sampling temperature |

**Validation:** `max_tokens > 0`, `temperature` between 0.0 and 1.0.

### Gateway Port

#### LlmGateway

| Method | Returns | Description |
|---|---|---|
| `generate(prompt, system_prompt, max_tokens, model)` | `LlmResponse` | Generate text from prompt |

**LlmResponse:** `text` (str), `model` (str), `usage` (Usage with `input_tokens`, `output_tokens`).

---

## Search Bounded Context

The Search context provides semantic search over indexed emails using
vector embeddings.

### Entities

#### SearchDocument

Indexed document for semantic search.

| Field | Type | Description |
|---|---|---|
| `id` | `UUIDId` | Local identifier |
| `email_id` | `UUIDId` | Referenced email |
| `content` | `str` | Text content to index |
| `embedding` | `list[float]` | Vector embedding |
| `metadata` | `dict[str, str]` | Subject, sender, date |
| `created_at` | `datetime` | Index timestamp |

### Gateway Port

#### EmbeddingGateway

| Method | Returns | Description |
|---|---|---|
| `embed(text)` | `list[float]` | Generate text embedding |
| `dimension()` | `int` | Embedding vector dimension |

### Repository Port

#### VectorSearchRepository

| Method | Returns | Description |
|---|---|---|
| `index(document)` | `None` | Index document for search |
| `search(query_vector, limit, min_score)` | `list[SearchResult]` | Similarity search |
| `delete(email_id)` | `None` | Remove indexed document |
| `count()` | `int` | Total indexed documents |

**SearchResult:** `document_id` (UUIDId), `email_id` (UUIDId), `score` (float), `metadata` (dict[str, str]).

---

## Notification Bounded Context

The Notification context handles outbound notifications for important emails,
inbox changes, and periodic digests.

### Domain Events

| Event | Fields | Description |
|---|---|---|
| `ImportantEmailDetected` | `email_id`, `from_address`, `subject`, `priority`, `detected_at` | High-priority email detected |
| `InboxChanged` | `event_type`, `email_id`, `changed_at` | Any inbox mutation |
| `DigestReady` | `digest_type`, `digest_period`, `email_count`, `generated_at` | Periodic digest generated |

**Validation:**
- `ImportantEmailDetected.priority`: 1-5
- `DigestReady.digest_type`: `daily` or `weekly`

### Gateway Port

#### NotificationGateway

| Method | Returns | Description |
|---|---|---|
| `send(title, body, channel)` | `bool` | Send notification |
| `publish(event_type, payload)` | `bool` | Publish event to channel |

---

## Aggregate Boundaries

```
Gmail Context:
  Email (aggregate root) --- 1..* --- Attachment (entity)
  Thread (aggregate root) --- 1..* --- Email (reference by ID)
  Label (entity, standalone)

Intelligence Context:
  Summary (entity) --> Email (reference by ID, external)
  Classification (entity) --> Email (reference by ID, external)
  Suggestion (entity) --> Email (reference by ID, external)

Search Context:
  SearchDocument (entity) --> Email (reference by ID, external)

Notification Context:
  Events only, no aggregates
```

Cross-context references use UUID IDs, not entity references. Each bounded
context is independently persistent and queryable.
