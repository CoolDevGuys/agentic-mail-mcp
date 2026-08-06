# project-structure Specification

## Purpose
Defines the DDD + vertical-slice directory layout for each bounded context and shared module.

## Requirements

### Requirement: Bootstrap module structure
The agentic_mail_mcp/Bootstrap/ directory SHALL contain __init__.py and stub modules for Settings.py, Logging.py, Lifespan.py, and DependencyContainer.py.

#### Scenario: Bootstrap files exist
- **WHEN** agentic_mail_mcp/Bootstrap/ is listed
- **THEN** __init__.py, Settings.py, Logging.py, Lifespan.py, DependencyContainer.py are present

### Requirement: Common module structure
The agentic_mail_mcp/Common/ directory SHALL contain Domain/ (ValueObjects/, Exceptions/, Events/, Specifications/, Repository/) and Infrastructure/ (Persistence/Migrations/, Messaging/, LLM/, Clock/, IdGenerator/) subdirectories with __init__.py files.

#### Scenario: Common directories exist
- **WHEN** agentic_mail_mcp/Common/ is traversed
- **THEN** all expected subdirectories contain __init__.py

### Requirement: Gmail bounded context structure
The agentic_mail_mcp/Gmail/ directory SHALL contain Domain/ (Entities/, ValueObjects/, Repository/, Gateway/, Mapper/, Events/) and Application/ (UseCases/, DTO/, Commands/, Queries/, Handlers/) and Infrastructure/ (Google/, Persistence/SqlAlchemy/Models/, Persistence/SqlAlchemy/Repositories/, Persistence/SqlAlchemy/Mappers/, Persistence/PostgreSQL/, MCP/) subdirectories.

#### Scenario: Gmail directories exist
- **WHEN** agentic_mail_mcp/Gmail/ is traversed
- **THEN** all Domain, Application, and Infrastructure subdirectories exist with __init__.py

### Requirement: Intelligence bounded context structure
The agentic_mail_mcp/Intelligence/ directory SHALL contain Domain/ (Entities/, Repository/, Gateway/, ValueObjects/), Application/ (UseCases/, DTO/), and Infrastructure/ (LlamaCpp/) subdirectories.

#### Scenario: Intelligence directories exist
- **WHEN** agentic_mail_mcp/Intelligence/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: Search bounded context structure
The agentic_mail_mcp/Search/ directory SHALL contain Domain/ (Repository/, Gateway/, Entities/), Application/ (UseCases/), and Infrastructure/ (PgVector/, BGE/) subdirectories.

#### Scenario: Search directories exist
- **WHEN** agentic_mail_mcp/Search/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: Notification bounded context structure
The agentic_mail_mcp/Notification/ directory SHALL contain Domain/ (Gateway/, Events/), Application/ (UseCases/), and Infrastructure/ (RabbitMQ/, Redis/, Webhook/) subdirectories.

#### Scenario: Notification directories exist
- **WHEN** agentic_mail_mcp/Notification/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: MCP module structure
The agentic_mail_mcp/MCP/ directory SHALL contain __init__.py and stub files for Server.py, ToolRegistry.py, Resources.py, Prompts.py, and Tools/ directory.

#### Scenario: MCP files exist
- **WHEN** agentic_mail_mcp/MCP/ is listed
- **THEN** Server.py, ToolRegistry.py, Resources.py, Prompts.py are present
