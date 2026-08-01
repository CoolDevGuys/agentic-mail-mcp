```
gmail-mcp-server/
|
|-- pyproject.toml
|-- gmail-api.iml
|-- Dockerfile
|-- docker-compose.yml
|-- .env
|-- .env.example
|-- README.md
|-- alembic.ini
|
|-- specs/
|   |
|   |-- docs/
|   |   |-- architecture.md
|   |   |-- domain-model.md
|   |   |-- events.md
|   |   |-- implementation_plan.md
|   |   |-- project_structure.md
|   |   |-- project.md
|   |   |-- project_brainstorming.md
|   |   |-- adr/
|   |       |-- 0001-shared-primitives.md
|   |
|   |-- guidelines/
|       |-- backend-standards.md
|       |-- documentation-standards.md
|       |-- testing-standards.md
|       |-- git-workflow.md
|       |-- security-guidelines.md
|
|-- tests/
|   |-- conftest.py
|   |-- unit/
|   |   |-- common/
|   |   |-- gmail/
|   |   |   |-- domain/
|   |   |       |-- value_objects/
|   |   |       |-- entities/
|   |   |-- intelligence/
|   |   |   |-- domain/
|   |   |-- search/
|   |   |   |-- domain/
|   |   |-- notification/
|   |       |-- domain/
|   |-- integration/
|   |-- fakes/
|
`-- src/
    |
    |-- Bootstrap/
    |   |-- __init__.py
    |   |-- cli.py
    |   |-- DependencyContainer.py
    |   |-- Logging.py
    |   |-- Lifespan.py
    |   `-- Settings.py
    |
    |-- Common/
    |   |-- __init__.py
    |   |
    |   |-- Domain/
    |   |   |-- __init__.py
    |   |   |-- ValueObjects/
    |   |   |   |-- __init__.py
    |   |   |   |-- base.py
    |   |   |   `-- uuid_id.py
    |   |   |-- Exceptions/
    |   |   |   `-- __init__.py
    |   |   |-- Events/
    |   |   |   `-- __init__.py
    |   |   |-- Specifications/
    |   |   |   `-- __init__.py
    |   |   `-- Repository/
    |   |       `-- __init__.py
    |   |
    |   `-- Infrastructure/
    |       |-- __init__.py
    |       |-- Persistence/
    |       |   |-- __init__.py
    |       |   `-- Migrations/
    |       |       `-- __init__.py
    |       |-- Messaging/
    |       |   `-- __init__.py
    |       |-- LLM/
    |       |   `-- __init__.py
    |       |-- Clock/
    |       |   `-- __init__.py
    |       `-- IdGenerator/
    |           `-- __init__.py
    |
    |-- Gmail/
    |   |-- __init__.py
    |   |
    |   |-- Domain/
    |   |   |-- __init__.py
    |   |   |-- Entities/
    |   |   |   |-- __init__.py
    |   |   |   |-- email.py
    |   |   |   |-- thread.py
    |   |   |   |-- attachment.py
    |   |   |   `-- label.py
    |   |   |-- ValueObjects/
    |   |   |   |-- __init__.py
    |   |   |   |-- email_address.py
    |   |   |   |-- gmail_message_id.py
    |   |   |   |-- thread_id.py
    |   |   |   |-- history_id.py
    |   |   |   `-- gmail_query.py
    |   |   |-- Repository/
    |   |   |   |-- __init__.py
    |   |   |   |-- email_repository.py
    |   |   |   `-- thread_repository.py
    |   |   |-- Gateway/
    |   |   |   |-- __init__.py
    |   |   |   `-- gmail_gateway.py
    |   |   |-- Mapper/
    |   |   |   |-- __init__.py
    |   |   |   |-- email_mapper.py
    |   |   |   `-- thread_mapper.py
    |   |   `-- Events/
    |   |       `-- __init__.py
    |   |
    |   |-- Application/
    |   |   |-- __init__.py
    |   |   |-- UseCases/
    |   |   |   `-- __init__.py
    |   |   |-- DTO/
    |   |   |   `-- __init__.py
    |   |   |-- Commands/
    |   |   |   `-- __init__.py
    |   |   |-- Queries/
    |   |   |   `-- __init__.py
    |   |   `-- Handlers/
    |   |       `-- __init__.py
    |   |
    |   `-- Infrastructure/
    |       |-- __init__.py
    |       |-- Google/
    |       |   `-- __init__.py
    |       |-- Persistence/
    |       |   |-- __init__.py
    |       |   |-- SqlAlchemy/
    |       |   |   |-- __init__.py
    |       |   |   |-- Models/
    |       |   |   |   `-- __init__.py
    |       |   |   |-- Repositories/
    |       |   |   |   `-- __init__.py
    |       |   |   `-- Mappers/
    |       |   |       `-- __init__.py
    |       |   `-- PostgreSQL/
    |       |       `-- __init__.py
    |       `-- MCP/
    |           `-- __init__.py
    |
    |-- Intelligence/
    |   |-- __init__.py
    |   |
    |   |-- Domain/
    |   |   |-- __init__.py
    |   |   |-- Entities/
    |   |   |   |-- __init__.py
    |   |   |   |-- summary.py
    |   |   |   |-- classification.py
    |   |   |   `-- suggestion.py
    |   |   |-- ValueObjects/
    |   |   |   |-- __init__.py
    |   |   |   |-- prompt_template.py
    |   |   |   `-- model_config.py
    |   |   |-- Repository/
    |   |   |   `-- __init__.py
    |   |   `-- Gateway/
    |   |       |-- __init__.py
    |   |       `-- llm_gateway.py
    |   |
    |   |-- Application/
    |   |   |-- __init__.py
    |   |   |-- UseCases/
    |   |   |   `-- __init__.py
    |   |   `-- DTO/
    |   |       `-- __init__.py
    |   |
    |   `-- Infrastructure/
    |       |-- __init__.py
    |       `-- LlamaCpp/
    |           `-- __init__.py
    |
    |-- Search/
    |   |-- __init__.py
    |   |
    |   |-- Domain/
    |   |   |-- __init__.py
    |   |   |-- Entities/
    |   |   |   |-- __init__.py
    |   |   |   `-- search_document.py
    |   |   |-- Repository/
    |   |   |   |-- __init__.py
    |   |   |   `-- vector_search_repository.py
    |   |   `-- Gateway/
    |   |       |-- __init__.py
    |   |       `-- embedding_gateway.py
    |   |
    |   |-- Application/
    |   |   |-- __init__.py
    |   |   `-- UseCases/
    |   |       `-- __init__.py
    |   |
    |   `-- Infrastructure/
    |       |-- __init__.py
    |       |-- SqliteVSS/
    |       |   `-- __init__.py
    |       |-- PgVector/
    |       |   `-- __init__.py
    |       `-- BGE/
    |           `-- __init__.py
    |
    |-- Notification/
    |   |-- __init__.py
    |   |
    |   |-- Domain/
    |   |   |-- __init__.py
    |   |   |-- Events/
    |   |   |   |-- __init__.py
    |   |   |   |-- important_email_detected.py
    |   |   |   |-- inbox_changed.py
    |   |   |   `-- digest_ready.py
    |   |   `-- Gateway/
    |   |       |-- __init__.py
    |   |       `-- notification_gateway.py
    |   |
    |   |-- Application/
    |   |   |-- __init__.py
    |   |   `-- UseCases/
    |   |       `-- __init__.py
    |   |
    |   `-- Infrastructure/
    |       |-- __init__.py
    |       |-- RabbitMQ/
    |       |   `-- __init__.py
    |       |-- Redis/
    |       |   `-- __init__.py
    |       `-- Webhook/
    |           `-- __init__.py
    |
    `-- MCP/
        |-- __init__.py
        |-- Server.py
        |-- ToolRegistry.py
        |-- Resources.py
        |-- Prompts.py
        `-- Tools/
            `-- __init__.py
```
