# Domain Events

> This document catalogs all domain events in the system, their payloads,
> producers, and consumers. Events are the primary communication mechanism
> between bounded contexts.

---

## Infrastructure

All domain events inherit from `DomainEvent` (`src/Common/Domain/Events/`):

| Field | Type | Description |
|---|---|---|
| `event_id` | `UUID` | Unique identifier, auto-generated (UUID4) |
| `occurred_at` | `datetime` | UTC-aware timestamp, auto-generated |
| `aggregate_id` | `UUIDId` | Identifier of the aggregate that raised the event |

Events are published through the `EventBus` protocol. The current implementation
is `InMemoryEventBus`, a synchronous, in-memory bus suitable for tests and
lightweight deployments. External bus adapters are planned for Phase 5.

---

## Gmail Context

### EmailReceived

Raised when a new email is persisted to the local store.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `from_address` | `str` |
| `subject` | `str` |
| `received_at` | `datetime` |

**Producers:** `SynchronizeInboxUseCase`, `GmailHistorySynchronizer`
**Consumers:** `NotifyImportantEmailUseCase`, `IndexEmailUseCase`, `AuditLogHandler`

### EmailArchived

Raised when an email is moved out of the inbox.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `archived_at` | `datetime` |

**Producers:** `ArchiveEmailUseCase`
**Consumers:** `AuditLogHandler`, `PublishInboxEventUseCase`

### EmailDeleted

Raised when an email is trashed or permanently deleted.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `deleted_at` | `datetime` |

**Producers:** `DeleteEmailUseCase`
**Consumers:** `AuditLogHandler`, `PublishInboxEventUseCase`

### EmailForwarded

Raised after a forwarded message is successfully sent.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `forwarded_to` | `str` |
| `forwarded_at` | `datetime` |

**Producers:** `ForwardEmailUseCase`
**Consumers:** `AuditLogHandler`, `PublishInboxEventUseCase`

### EmailLabeled

Raised when a label is added to or removed from an email.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `label_name` | `str` |
| `labeled_at` | `datetime` |

**Producers:** Use cases that modify labels
**Consumers:** `AuditLogHandler`, `PublishInboxEventUseCase`

### InboxSynchronized

Raised after a batch of Gmail history changes is processed.

| Field | Type |
|---|---|
| `history_id` | `str` |
| `synchronized_at` | `datetime` |
| `email_count` | `int` |

**Producers:** `GmailHistorySynchronizer`
**Consumers:** Monitoring, statistics

---

## Notification Context

### ImportantEmailDetected

Raised when an incoming email is classified as important.

| Field | Type |
|---|---|
| `email_id` | `UUIDId` |
| `from_address` | `str` |
| `subject` | `str` |
| `priority` | `int` |
| `detected_at` | `datetime` |

**Producers:** `ClassifyEmailUseCase`
**Consumers:** `NotifyImportantEmailUseCase`

### InboxChanged

Raised on any inbox mutation (archive, delete, label, read).

| Field | Type |
|---|---|
| `event_type` | `str` |
| `email_id` | `UUIDId` |
| `changed_at` | `datetime` |

**Producers:** Gmail write use cases
**Consumers:** `PublishInboxEventUseCase`

### DigestReady

Raised when a daily or weekly digest is generated.

| Field | Type |
|---|---|
| `digest_type` | `str` |
| `digest_period` | `str` |
| `email_count` | `int` |
| `generated_at` | `datetime` |

**Producers:** `DailyDigestUseCase`, `WeeklyDigestUseCase`
**Consumers:** `PublishInboxEventUseCase`

---

## Event Flow

```
Aggregate raises event → EventBus.publish() → Handlers execute
```

Handlers execute synchronously in subscription order. External bus adapters
(Phase 5) may introduce async dispatch.
