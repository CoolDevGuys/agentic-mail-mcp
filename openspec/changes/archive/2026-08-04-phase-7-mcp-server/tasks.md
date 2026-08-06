## 1. MCP Server Bootstrap (7.1)

- [x] 1.1 Implement `MCP/Server.py`: `create_server(container)` assembling the server from the DI container and resolving settings/services
- [x] 1.2 Wire configurable transport — `stdio` default, HTTP when `Settings.mcp` provides host/port — isolating all `mcp`-library calls in this module
- [x] 1.3 Integrate `Bootstrap/Lifespan.py` so startup/shutdown hooks run around the server lifecycle
- [x] 1.4 Point the `agentic-mail-mcp` console entry point at the server launch
- [x] 1.5 Write tests: server builds from container, starts/stops cleanly, default transport is stdio, HTTP selected when configured

## 2. Tool Registry with Access-Level Gating (7.2)

- [x] 2.1 Implement `MCP/ToolRegistry.py`: register tools with name, agent-friendly description, JSON-Schema input schema, grouped by category (read/write/intelligence/search)
- [x] 2.2 Read `Settings.railguards.access_level` at registration; skip the entire write category when `read_only`
- [x] 2.3 Implement a shared error-to-tool-result mapper covering `PermissionError`, `NotFoundError`, `ValidationError`
- [x] 2.4 Write tests: all tools registered when `read_write`, write tools absent when `read_only`, read/intelligence/search present when `read_only`, schemas valid

## 3. Read Tools (7.3)

- [x] 3.1 Implement `SearchEmailsTool` wrapping `SearchEmailsUseCase` (params: query, from, to, subject, date range, label, unread, page, page_size)
- [x] 3.2 Implement `GetEmailTool`, `GetThreadTool`, `ListUnreadTool`, `ListLabelsTool` wrapping their use cases
- [x] 3.3 Write tests: tool-to-use-case wiring, parameter validation, invalid-argument rejection without invoking the use case

## 4. AddLabelUseCase (gmail-application delta)

- [x] 4.1 Implement railguarded `AddLabelUseCase` consuming `AddLabelCommand`: validate → `GmailGateway.modify_message` (add label) → emit `EmailLabeled`
- [x] 4.2 Write tests: label applied and `EmailLabeled` published when permitted, `PermissionError` when read-only (no gateway call/event), no event when gateway fails

## 5. Write Tools with Railguards (7.4)

- [x] 5.1 Implement `ForwardEmailTool`, `ArchiveEmailTool`, `DeleteEmailTool` wrapping their railguarded use cases
- [x] 5.2 Implement `CreateDraftTool`, `SendDraftTool`, `AddLabelTool` wrapping their use cases
- [x] 5.3 Write tests: railguard denial (`PermissionError`) surfaces as a structured tool error; command construction from tool arguments

## 6. Intelligence Tools (7.5)

- [x] 6.1 Implement `SummarizeEmailTool`, `ClassifyEmailTool`, `SuggestReplyTool`, `ExtractActionItemsTool` wrapping their use cases
- [x] 6.2 Implement `DailyDigestTool` (param: date) and `WeeklyDigestTool` (param: week_start)
- [x] 6.3 Write tests: LLM integration via tools using the fake LLM gateway

## 7. Search Tools (7.6)

- [x] 7.1 Implement `SemanticSearchTool` wrapping `SemanticSearchUseCase` (params: query, limit, min_score)
- [x] 7.2 Write tests: semantic search via tool using fake embedding + vector repo

## 8. Resources (7.7)

- [x] 8.1 Implement `MCP/Resources.py`: account-info (account + access level), watch-status (Gmail push state), index-status (vector index statistics)
- [x] 8.2 Write tests: each resource is available and reports the expected fields

## 9. Prompts (7.8)

- [x] 9.1 Implement `MCP/Prompts.py`: search-strategy prompt and email-management workflow prompt via `PromptTemplate`
- [x] 9.2 Write tests: prompts render with no unresolved placeholders

## 10. Verification

- [x] 10.1 Run the full unit test suite and confirm coverage floors hold (≥90% Domain, ≥80% overall)
- [x] 10.2 Lint (ruff) and type-check (mypy) pass
- [x] 10.3 `openspec validate phase-7-mcp-server` passes
