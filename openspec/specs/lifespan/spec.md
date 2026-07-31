## ADDED Requirements

### Requirement: Async lifespan context manager
The Lifespan module SHALL provide an async def lifespan(app) context manager for application lifecycle management.

#### Scenario: Lifespan is a context manager
- **WHEN** lifespan(app) is used in an async with block
- **THEN** startup code runs before yield, shutdown code runs after

### Requirement: Startup initialization
During startup, the lifespan SHALL initialize the DB connection pool, warm the OAuth token, and register domain event handlers.

#### Scenario: Startup completes
- **WHEN** the context manager enters
- **THEN** DB pool is initialized, OAuth token is warmed, event handlers are registered

### Requirement: Shutdown cleanup
During shutdown, the lifespan SHALL close DB connections, flush the audit log, and unsubscribe from Gmail push notifications.

#### Scenario: Shutdown completes
- **WHEN** the context manager exits
- **THEN** DB connections are closed, audit log is flushed, Gmail watch is stopped

### Requirement: MCP server integration
The lifespan SHALL integrate with the MCP server lifecycle.

#### Scenario: MCP server uses lifespan
- **WHEN** the MCP server starts
- **THEN** the lifespan context manager is used for setup/teardown
