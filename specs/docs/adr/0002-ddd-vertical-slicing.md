# 0002 — DDD with Vertical Slicing

Status: accepted

Context: The server spans several distinct concerns — Gmail mailbox operations, LLM-powered intelligence, semantic search, and notifications — each with its own model, external systems, and rate of change. A conventional layered/technical layout (all entities together, all repositories together, all services together) would scatter each feature across the tree and couple unrelated concerns through shared "service" and "model" packages. We need a structure that keeps a feature's domain, application, and infrastructure close, enforces the dependency rule, and lets contexts evolve independently.

Decision: The codebase is organized by **bounded context** (vertical slices), not by technical layer. Under `agentic_mail_mcp/` each context — `Gmail/`, `Intelligence/`, `Search/`, `Notification/` — owns its full stack: `Domain/` (entities, value objects, events, ports), `Application/` (use cases, DTOs, commands/queries), and `Infrastructure/` (adapters). `Common/` holds shared domain primitives (see [ADR 0001](0001-shared-primitives.md)); `Bootstrap/` holds composition (settings, DI container, lifespan, CLI); `MCP/` is the interface layer that adapts use cases to the protocol. The dependency rule points inward: Domain depends on nothing, Application depends on Domain, Infrastructure and MCP depend on Application/Domain via ports — never the reverse. Contexts communicate through domain events on the `EventBus`, not by importing each other's internals.

Consequences:

- **Easier:** A feature change touches one slice. Contexts are testable in isolation with in-memory fakes at their ports. The dependency rule is checkable (Domain never imports Infrastructure), and a context can swap adapters (SQLite ↔ PostgreSQL, stdio ↔ HTTP) without touching its domain.
- **Harder:** More directories and `__init__.py` files; cross-context flows go through events rather than direct calls, which is more indirection to trace. Shared concepts must be deliberately placed in `Common/` rather than casually reused across contexts.
- **Future:** A new bounded context is added as a new slice without disturbing existing ones. Extracting a context into its own service later is tractable because its boundary is already explicit.
