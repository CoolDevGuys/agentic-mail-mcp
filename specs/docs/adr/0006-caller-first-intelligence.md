# 0006 — Caller-First Intelligence

Status: accepted

Context: The server exposes "intelligence" features — summarize, classify, suggest a reply, extract action items, and daily/weekly digests. The obvious implementation is a tool that calls a configured LLM. But this server's consumer *is* an LLM/agent. Making a tool that calls a second LLM is redundant, and because MCP tool calls are synchronous from the agent's perspective, an internal LLM call serializes an extra generation into the agent's wait — turning a ~200 ms data tool into a multi-second one. It also doubles inference cost and forces an API key, which fights the goal of a fast, low-configuration setup.

Decision: **Caller-first.** Per-email reasoning is exposed as **MCP prompts** (`summarize_email`, `classify_email`, `draft_reply`, `extract_action_items`) that the calling agent runs on data it fetches with `get_email` — no server-side inference, no added latency, no key required. Internal LLM inference is reserved for the cases where it genuinely earns its keep:

- **Digests** (`daily_digest` / `weekly_digest`) map-reduce over many emails, which is real context/token savings for the agent. They register **only when an LLM is configured** (`llm.api_key`, or `model_path` for llamacpp).
- **Embeddings** for semantic search stay server-side (the caller cannot embed, and MCP has no embeddings primitive).
- The per-email tools remain available as an **opt-in escape hatch** (`llm.internal_tools=true`) for deployments that want consistent server-side processing regardless of caller.

MCP **sampling** (server requests the client's LLM) was considered for the per-email case and rejected as the default: client support is inconsistent, and it still adds a round-trip to hand data back to an agent that is about to reason over it anyway.

Consequences:

- **Easier:** Zero-LLM quick start — the core Gmail experience needs no API key. Tool latency stays low. No double inference cost. The caller's (usually stronger) model does the reasoning.
- **Harder:** Two "shapes" for intelligence (prompts vs. the opt-in tools) to document and keep coherent. Per-email intelligence quality now depends on the caller honoring the prompts rather than a fixed server prompt.
- **Future:** A sampling-backed mode can be added behind the same `internal_tools` switch if broad client support arrives; digests can gain caching/async execution without changing the tool contract.
