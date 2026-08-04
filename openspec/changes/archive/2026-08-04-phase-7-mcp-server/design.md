## Context

Phases 1–6 built the full application stack: domain models, read use cases (Phase 4), intelligence and search use cases (4b/4c), infrastructure adapters (Phase 5), and the railguards framework with railguarded write use cases and `RailguardValidator` (Phase 6). The DI container (`Bootstrap/DependencyContainer.py`), async `Lifespan` (`Bootstrap/Lifespan.py`), and typed `Settings` (with `mcp` and `railguards` sections) already exist. The `mcp` package is declared in `pyproject.toml`, and `gmail-mcp-server` is registered as a console entry point.

What is missing is the outermost layer. `src/MCP/` contains only stubs: `Server.py` returns a bare server, `ToolRegistry.py` is a dict wrapper, and `Resources.py`/`Prompts.py` are empty. Nothing wires the use cases to the MCP protocol, so no AI agent can call the server. Phase 7 closes that gap.

One incidental gap: Phase 7.4 specifies an `AddLabelTool` wrapping `AddLabelUseCase`, but only `AddLabelCommand` exists — the use case was never built. It is small and railguarded like the other writes, so it is folded into this change.

## Goals / Non-Goals

**Goals:**
- Stand up a runnable MCP server that boots from the DI container and integrates the existing `Lifespan`, with `stdio` as the default transport and HTTP selectable via `Settings.mcp`.
- Expose the read, write, intelligence, and search use cases as MCP tools with clear, agent-friendly descriptions and JSON-Schema input schemas.
- Enforce defense-in-depth: when `access_level=read_only`, write tools are **never registered**, so they are invisible to the agent — not merely denied at execution.
- Expose account/watch/index status as MCP resources and ship a few workflow prompts.
- Keep tools thin: each tool validates/parses input, invokes exactly one use case, and maps the result (or raised `PermissionError`/domain error) to an MCP response.

**Non-Goals:**
- Changing any use case, gateway, repository, or railguard contract — Phase 7 is a consumer of Phase 1–6, not a modifier (except adding `AddLabelUseCase`).
- Full API documentation (`specs/docs/api.md`), PyPI/Docker packaging, and E2E tests — those are Phase 8.
- New transports beyond stdio/HTTP, authn/z beyond the railguard access level, or streaming tool responses.
- Server-side Gmail filter rules (out of V1 scope).

## Decisions

**1. The server is assembled from the DI container; tools resolve use cases lazily.**
`create_server(container)` reads `Settings` and the registered services from the container, builds the `ToolRegistry`, and registers resources and prompts. Each tool holds a reference to the container (or a use-case factory) and resolves its use case when invoked, so construction stays cheap and testable. Alternative (tools construct their own dependencies) rejected: duplicates wiring and defeats the container.

**2. `stdio` is the default transport; HTTP is opt-in via `Settings.mcp`.**
AI-agent harnesses speak stdio, so it is the default. `Settings.mcp` (host/port) selects HTTP when configured. The transport choice lives in `Server.py` and does not leak into tools. Alternative (HTTP default) rejected: stdio is the primary distribution mode for agent harnesses.

**3. Lifespan integration wraps the MCP server lifecycle.**
The MCP server runs inside the `Bootstrap/Lifespan.py` async context manager, so DB pools warm and OAuth tokens load on startup and flush/close on shutdown, exactly as designed in Phase 1.5. The server does not re-implement resource setup.

**4. Registry gates write tools at registration time (defense-in-depth).**
`ToolRegistry` groups tools by category (`read`, `write`, `intelligence`, `search`). At registration it reads `Settings.railguards.access_level`; when `read_only`, it **skips the entire write category**, so `ForwardEmailTool`, `ArchiveEmailTool`, `DeleteEmailTool`, `CreateDraftTool`, `SendDraftTool`, and `AddLabelTool` are absent from the exposed tool list. This is layered on top of — not a replacement for — `RailguardValidator`, which still guards execution when `read_write`. Alternative (register all, deny at runtime) rejected: it exposes destructive tools to the agent and leaks their existence.

**5. Tools are thin adapters, one use case each.**
Every tool: (a) declares a JSON-Schema input schema, (b) parses/validates arguments into the use case's query/command object, (c) invokes the single use case, (d) serializes the returned DTO to the tool result, and (e) maps `PermissionError` (railguard denial) and domain errors (`NotFoundError`, `ValidationError`) to structured MCP tool errors. No business logic lives in tools. This keeps the layer testable purely by asserting the wiring and the error mapping.

**6. `AddLabelUseCase` mirrors the other railguarded writes.**
It consumes the existing `AddLabelCommand`, calls `RailguardValidator.validate` first, applies the label via `GmailGateway.modify_message` (add label), and emits `EmailLabeled` after the gateway call succeeds — matching the Phase-6 pattern (validate → gateway → publish). This unblocks `AddLabelTool`.

**7. Resources are read-only projections; prompts are static templates.**
The account-info resource reports the connected account and current `access_level`; the watch-status resource reports Gmail push-notification state; the index-status resource reports vector-index statistics. Each reads from existing services (OAuth provider, watcher, vector repository). Prompts are pre-built templates (search-strategy, email-management workflow) rendered via the existing `PromptTemplate` mechanism.

## Risks / Trade-offs

- **MCP package API shape** → The `mcp` library's server/tool registration API must match the wrappers. Mitigation: isolate all `mcp`-specific calls in `Server.py`/`ToolRegistry.py` so tool logic is library-agnostic and unit-testable without a live protocol.
- **Access-level read at registration is a snapshot** → If `access_level` changes at runtime, the registered tool set does not update. Acceptable: access level is deployment configuration, not runtime state; a restart re-registers. Documented.
- **Thin tools still need faithful error mapping** → A missed `PermissionError` mapping could leak a stack trace to the agent. Mitigation: a shared error-to-tool-result mapper covering `PermissionError`, `NotFoundError`, and `ValidationError`, with tests per category.
- **`AddLabelUseCase` widens Phase-7 scope beyond pure MCP wiring** → Small and necessary (the tool cannot wrap a non-existent use case); implemented with the established railguard pattern and its own tests.

## Migration Plan

Purely additive. Replace the four `src/MCP/` stubs with implementations and add `src/MCP/Tools/` modules; add `AddLabelUseCase` under `src/Gmail/Application/UseCases/`. No schema, data, or config-default changes. The `gmail-mcp-server` console entry point begins launching a functional server. Land in order: (1) `Server.py` + transport + lifespan, (2) `ToolRegistry` with access-level gating, (3) read tools, (4) `AddLabelUseCase` + write tools, (5) intelligence + search tools, (6) resources + prompts — each independently testable with the in-memory event bus and fakes. Rollback is reverting the change; Phases 1–6 remain intact and usable.

## Open Questions

- Does the pinned `mcp` package expose tool registration as a decorator, an imperative `add_tool`, or both? Resolve against the installed version before writing `ToolRegistry`; keep the wrapper adaptable.
- Should HTTP transport ship in this phase or be stubbed behind the setting until Phase 8 packaging? Leaning: implement both, since `Settings.mcp` already models host/port and stdio-only would leave the setting inert.
- Resource payload shape (raw dict vs. typed DTO serialized to JSON) — leaning JSON of a small typed DTO per resource for consistency with tool results.
