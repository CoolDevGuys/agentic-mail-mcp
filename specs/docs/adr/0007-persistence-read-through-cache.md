# 0007 — Persistence as a Read-Through Cache, Not a Mirror

Status: accepted

Context: The server needs local persistence for identity, list views, and speed, but its data lives in Gmail. A natural instinct is to mirror the mailbox locally and keep it in sync (deletes, moves, label and read-status changes) via the Gmail History API and push notifications. A mirror, however, is perpetually one event behind — a permanent source of "the agent acted on stale state" bugs — and it duplicates potentially sensitive email content at rest. For a security-conscious, agent-facing tool the cost/benefit is poor.

Decision: **Gmail is the source of truth; local persistence is a read-through cache and a set of derived stores, never a mirror.**

- **Identity is the Gmail `message_id`.** Tools speak `message_id` end to end (search returns it; `get_email` and the write tools accept it). The internal `UUID` is an implementation detail assigned by the cache and kept stable per message id.
- **Single-email reads are live.** `find_by_gmail_message_id` / `find_by_id` fetch from the gateway so callers get fresh, complete data (including the body).
- **Metadata-only at rest.** Cache rows store headers/labels/snippet — **never the body**. Bodies are fetched live on demand.
- **Short TTL for list views.** `list_unread` is served from the metadata cache, filtered by `database.cache_ttl_seconds` (default 900s). The freshness clock is in memory, so a restart conservatively treats the cache as stale.
- **Self-healing, no sync engine.** A message the gateway reports as gone (404 / `None`) is evicted and reported not-found. There is no delete-propagation job and no history sync.
- **Threads are not cached at all.** `get_thread` calls `GmailGateway.get_thread` (`users.threads.get`) directly on every call — there is no local sync engine populating a thread cache, so a cache-backed thread lookup would simply never find anything. This also means every message in the thread comes back with its full body already fetched, at the cost of a live round trip per call.
- The **audit log** (durable) and **search index** (durable, derived embeddings) are the only stores that intentionally outlive a TTL.

Consequences:

- **Easier:** No sync machinery to build or debug; reads are always consistent with Gmail; minimal sensitive content at rest (metadata, short-lived, gitignored/encryptable); `message_id`-everywhere removes the identity impedance between search and writes.
- **Harder:** Single-email operations always incur a live API call (acceptable for agent latencies). List views only reflect recently-seen emails within the TTL; the authoritative discovery path is the live `search_emails`. The Gmail→domain mapper must tolerate real-world header quirks (display-name senders) rather than assume bare addresses.
- **Future:** If durable local search over the whole mailbox is needed, an explicit indexing pass (already modeled by `IndexEmailUseCase`) can populate the store deliberately — still not a mirror, just a chosen projection.
