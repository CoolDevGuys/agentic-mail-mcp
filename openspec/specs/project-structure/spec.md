## ADDED Requirements

### Requirement: Bootstrap module structure
The src/Bootstrap/ directory SHALL contain __init__.py and stub modules for Settings.py, Logging.py, Lifespan.py, and DependencyContainer.py.

#### Scenario: Bootstrap files exist
- **WHEN** src/Bootstrap/ is listed
- **THEN** __init__.py, Settings.py, Logging.py, Lifespan.py, DependencyContainer.py are present

### Requirement: Common module structure
The src/Common/ directory SHALL contain Domain/ (ValueObjects/, Exceptions/, Events/, Specifications/, Repository/) and Infrastructure/ (Persistence/Migrations/, Messaging/, LLM/, Clock/, IdGenerator/) subdirectories with __init__.py files.

#### Scenario: Common directories exist
- **WHEN** src/Common/ is traversed
- **THEN** all expected subdirectories contain __init__.py

### Requirement: Gmail bounded context structure
The src/Gmail/ directory SHALL contain Domain/ (Entities/, ValueObjects/, Repository/, Gateway/, Mapper/, Events/) and Application/ (UseCases/, DTO/, Commands/, Queries/, Handlers/) and Infrastructure/ (Google/, Persistence/SqlAlchemy/Models/, Persistence/SqlAlchemy/Repositories/, Persistence/SqlAlchemy/Mappers/, Persistence/PostgreSQL/, MCP/) subdirectories.

#### Scenario: Gmail directories exist
- **WHEN** src/Gmail/ is traversed
- **THEN** all Domain, Application, and Infrastructure subdirectories exist with __init__.py

### Requirement: Intelligence bounded context structure
The src/Intelligence/ directory SHALL contain Domain/ (Entities/, Repository/, Gateway/, ValueObjects/), Application/ (UseCases/, DTO/), and Infrastructure/ (LlamaCpp/) subdirectories.

#### Scenario: Intelligence directories exist
- **WHEN** src/Intelligence/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: Search bounded context structure
The src/Search/ directory SHALL contain Domain/ (Repository/, Gateway/, Entities/), Application/ (UseCases/), and Infrastructure/ (PgVector/, BGE/) subdirectories.

#### Scenario: Search directories exist
- **WHEN** src/Search/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: Notification bounded context structure
The src/Notification/ directory SHALL contain Domain/ (Gateway/, Events/), Application/ (UseCases/), and Infrastructure/ (RabbitMQ/, Redis/, Webhook/) subdirectories.

#### Scenario: Notification directories exist
- **WHEN** src/Notification/ is traversed
- **THEN** all expected subdirectories exist with __init__.py

### Requirement: MCP module structure
The src/MCP/ directory SHALL contain __init__.py and stub files for Server.py, ToolRegistry.py, Resources.py, Prompts.py, and Tools/ directory.

#### Scenario: MCP files exist
- **WHEN** src/MCP/ is listed
- **THEN** Server.py, ToolRegistry.py, Resources.py, Prompts.py are present
