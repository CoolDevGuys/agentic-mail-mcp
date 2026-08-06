## Why

The Gmail MCP Server project needs a solid foundation before any domain logic can be built. Without proper project structure, configuration management, logging, dependency injection, testing infrastructure, and CI/CD, development of subsequent phases will be slow, error-prone, and hard to maintain.

## What Changes

- Create `pyproject.toml` with project metadata, dependencies, build system, and entry points
- Bootstrap the full `src/` directory tree following DDD + bounded context architecture
- Implement configuration layer via pydantic-settings (`Bootstrap/Settings.py`)
- Implement structured JSON logging with sensitive data redaction (`Bootstrap/Logging.py`)
- Implement async application lifespan management (`Bootstrap/Lifespan.py`)
- Implement lightweight DI container (`Bootstrap/DependencyContainer.py`)
- Set up testing infrastructure (pytest, fakes, coverage floors)
- Create Docker setup (Dockerfile, docker-compose, health checks)
- Create CI/CD pipeline (lint, type-check, test, security scanning, publish)

## Capabilities

### New Capabilities
- `project-config`: pyproject.toml with metadata, dependencies, build system (hatchling), entry points, and optional extras
- `project-structure`: Full src/ directory tree with DDD bounded contexts (Bootstrap, Common, Gmail, Intelligence, Search, Notification, MCP)
- `settings`: Pydantic-settings based configuration with .env support, AGENTIC_MAIL_MCP_ prefix, and documented .env.example
- `logging`: Structured JSON logging with correlation IDs, timestamps, and sensitive data redaction
- `lifespan`: Async application lifecycle management (startup/shutdown) with DB, OAuth, and event bus integration
- `dependency-injection`: Lightweight dict-based DI container with factory/async-factory support
- `testing-infra`: pytest configuration, shared fixtures, fake implementations, and tiered coverage floors
- `docker`: Dockerfile (Python 3.11 slim), docker-compose with optional PostgreSQL, health checks, .dockerignore
- `ci-cd`: GitHub Actions workflow (lint, type-check, test, security scan) with lockfile validation and release publishing

### Modified Capabilities

## Impact

- New files: `pyproject.toml`, `.env.example`, `Dockerfile`, `docker-compose.yml`, `.dockerignore`, `.github/workflows/ci.yml`, `pytest.ini`, `tests/conftest.py`, and full `src/` tree with `__init__.py` stubs
- New dependencies: mcp, google-api-python-client, google-auth-oauthlib, pydantic, pydantic-settings, aiosqlite, sqlalchemy, alembic, httpx, python-dotenv, pytest, pytest-asyncio, pytest-cov, ruff, mypy
- No existing code affected (greenfield foundation)
