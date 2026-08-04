## Why

Phases 1–6 delivered every domain, application use case, infrastructure adapter, and the railguards framework — but **none of it is reachable by an AI agent yet**. `src/MCP/` holds only stubs (`Server.py`, `ToolRegistry.py`, `Resources.py`, `Prompts.py`). Phase 7 builds the MCP server layer that exposes the existing read, write, intelligence, and search use cases as MCP tools, resources, and prompts, turning the codebase into a runnable Gmail MCP server.

## What Changes

- **MCP server bootstrap** (`MCP/Server.py`): builds the MCP server from the DI container, wires `Bootstrap/Lifespan.py` into the MCP lifecycle, and supports a configurable transport — `stdio` (default, for AI agent harnesses) or HTTP.
- **Tool registry** (`MCP/ToolRegistry.py`): registers tools with AI-agent-friendly descriptions and JSON-Schema input schemas, grouped by category (read, write, intelligence, search). **Defense-in-depth**: at registration time it reads `Settings.railguards.access_level` and **skips registering every write-category tool when access is `read_only`**, so write tools are never exposed to the agent — not merely blocked at execution by `RailguardValidator`.
- **Read tools**: `SearchEmailsTool`, `GetEmailTool`, `GetThreadTool`, `ListUnreadTool`, `ListLabelsTool` — each wrapping its Phase-4 read use case.
- **Write tools** (railguarded): `ForwardEmailTool`, `ArchiveEmailTool`, `DeleteEmailTool`, `CreateDraftTool`, `SendDraftTool`, `AddLabelTool` — each wrapping its Phase-6 railguarded write use case; railguard denials surface as tool errors.
- **Intelligence tools**: `SummarizeEmailTool`, `ClassifyEmailTool`, `SuggestReplyTool`, `ExtractActionItemsTool`, `DailyDigestTool`, `WeeklyDigestTool`.
- **Search tools**: `SemanticSearchTool`.
- **Resources** (`MCP/Resources.py`): account-info resource (connected account + access level), watch-status resource (Gmail push-notification status), and index-status resource (vector index statistics).
- **Prompts** (`MCP/Prompts.py`): pre-built prompts guiding agents to use the server effectively (e.g. a search-strategy prompt and an email-management workflow prompt).
- **`AddLabelUseCase`**: `AddLabelTool` requires a use case that does not yet exist (Phase 4 defined only `AddLabelCommand`); this change adds the railguarded `AddLabelUseCase` that consumes it and emits `EmailLabeled`.

## Capabilities

### New Capabilities
- `mcp-server`: the MCP server layer — server bootstrap with configurable stdio/HTTP transport and lifespan integration; a category-grouped tool registry that gates write tools behind `access_level` at registration time; the read, write, intelligence, and search tool wrappers; and the MCP resources and prompts.

### Modified Capabilities
- `gmail-application`: adds the railguarded `AddLabelUseCase` (consuming the existing `AddLabelCommand`, validated by `RailguardValidator`, emitting `EmailLabeled`), which `AddLabelTool` wraps.

## Impact

- Replaces the stubs in `src/MCP/` (`Server.py`, `ToolRegistry.py`, `Resources.py`, `Prompts.py`) with full implementations and adds tool modules under `src/MCP/Tools/` (one per tool, organized by category).
- Adds `AddLabelUseCase` under `src/Gmail/Application/UseCases/`.
- Consumes existing pieces without changing their contracts: the DI container (Phase 1.6), `Lifespan` (1.5), `Settings.railguards`/`Settings.mcp` (1.3), every read use case (Phase 4), the intelligence and search use cases (4b/4c), and the railguarded write use cases + `RailguardValidator` (Phase 6).
- Depends on the `mcp` package already declared in `pyproject.toml`; the `gmail-mcp-server` console entry point is wired to launch this server.
- Docs: `specs/docs/api.md` (tool/resource/prompt catalog) is Phase 8 and out of scope; this change adds unit tests for tool-to-use-case wiring, registry access-level gating, resource availability, and prompt rendering.
