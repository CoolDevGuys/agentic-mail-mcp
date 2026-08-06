## 1. Project Configuration

- [x] 1.1 Create pyproject.toml with project metadata (name: agentic-mail-mcp, version, description, authors, Python 3.11+ classifiers)
- [x] 1.2 Add build system configuration (hatchling) and core dependencies (mcp, google-api-python-client, google-auth-oauthlib, pydantic, pydantic-settings, aiosqlite, sqlalchemy, alembic, httpx, python-dotenv)
- [x] 1.3 Add optional extras: [postgresql] (asyncpg, psycopg2) and [dev] (pytest, pytest-asyncio, pytest-cov, ruff, mypy)
- [x] 1.4 Define console script entry point: agentic-mail-mcp

## 2. Project Structure

- [x] 2.1 Create src/Bootstrap/ with __init__.py and stub files (Settings.py, Logging.py, Lifespan.py, DependencyContainer.py)
- [x] 2.2 Create src/Common/ directory tree: Domain/ (ValueObjects/, Exceptions/, Events/, Specifications/, Repository/), Infrastructure/ (Persistence/Migrations/, Messaging/, LLM/, Clock/, IdGenerator/)
- [x] 2.3 Create src/Gmail/ directory tree: Domain/ (Entities/, ValueObjects/, Repository/, Gateway/, Mapper/, Events/), Application/ (UseCases/, DTO/, Commands/, Queries/, Handlers/), Infrastructure/ (Google/, Persistence/SqlAlchemy/Models/, Persistence/SqlAlchemy/Repositories/, Persistence/SqlAlchemy/Mappers/, Persistence/PostgreSQL/, MCP/)
- [x] 2.4 Create src/Intelligence/ directory tree: Domain/ (Entities/, Repository/, Gateway/, ValueObjects/), Application/ (UseCases/, DTO/), Infrastructure/ (LlamaCpp/)
- [x] 2.5 Create src/Search/ directory tree: Domain/ (Repository/, Gateway/, Entities/), Application/ (UseCases/), Infrastructure/ (PgVector/, BGE/)
- [x] 2.6 Create src/Notification/ directory tree: Domain/ (Gateway/, Events/), Application/ (UseCases/), Infrastructure/ (RabbitMQ/, Redis/, Webhook/)
- [x] 2.7 Create src/MCP/ with __init__.py and stubs (Server.py, ToolRegistry.py, Resources.py, Prompts.py, Tools/)
- [x] 2.8 Add __init__.py to all directories

## 3. Settings

- [x] 3.1 Implement Settings class inheriting from pydantic_settings.BaseSettings
- [x] 3.2 Define configuration sections: gmail, database, railguards, mcp, llm, notifications
- [x] 3.3 Add .env file support with AGENTIC_MAIL_MCP_ prefix environment variables
- [x] 3.4 Implement Settings.from_env() factory method
- [x] 3.5 Create .env.example with all keys documented and placeholder values

## 4. Logging

- [x] 4.1 Implement setup_logging(level, json_format) function
- [x] 4.2 Create JSON formatter with correlation_id, timestamp, level, module, message fields
- [x] 4.3 Implement redaction filter for tokens, passwords, and email bodies
- [x] 4.4 Wire log level to Settings.logging.level configuration

## 5. Lifespan

- [x] 5.1 Implement async def lifespan(app) context manager
- [x] 5.2 Implement startup: initialize DB connection pool, warm OAuth token, register domain event handlers
- [x] 5.3 Implement shutdown: close DB connections, flush audit log, unsubscribe from Gmail push notifications
- [x] 5.4 Integrate lifespan with MCP server lifecycle

## 6. Dependency Injection

- [x] 6.1 Implement Container class with register(), resolve(), singleton() methods
- [x] 6.2 Support sync factory functions and async factory functions
- [x] 6.3 Pre-register default services: settings, logger, DB session factory, event bus
- [x] 6.4 Add type-hinted resolution support

## 7. Testing Infrastructure

- [x] 7.1 Create pytest.ini with asyncio_mode=auto, testpaths, and markers
- [x] 7.2 Create tests/conftest.py with shared fixtures: settings, event_bus, clock, container
- [x] 7.3 Create tests/unit/ and tests/integration/ directories
- [x] 7.4 Create tests/fakes/ with FakeEmailRepository, FakeGmailGateway, FakeLlmGateway, FakeEmbeddingGateway, FakeNotificationGateway
- [x] 7.5 Configure pytest-cov with tiered floors: >=90% on Domain/, >=80% overall

## 8. Docker

- [x] 8.1 Create Dockerfile: Python 3.11 slim base, copy pyproject.toml, install deps, copy source, non-root user
- [x] 8.2 Create docker-compose.yml: agentic-mail-mcp service + optional postgres service
- [x] 8.3 Add health check on MCP server port
- [x] 8.4 Create .dockerignore excluding .venv, __pycache__, .git

## 9. CI/CD

- [x] 9.1 Create GitHub Actions workflow: lint (ruff), type-check (mypy), test (pytest with coverage) on push/PR
- [x] 9.2 Add dependency vulnerability scanning (pip-audit or Dependabot) on schedule and dependency changes
- [x] 9.3 Add lockfile validation in CI
- [x] 9.4 Add build/publish job gated on CI green, triggered on release tag
