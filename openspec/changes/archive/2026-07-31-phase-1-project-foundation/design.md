## Context

The Gmail MCP Server is a greenfield project designed to expose Gmail operations as MCP tools for AI agents. Phase 1 establishes the project foundation: build configuration, directory structure, configuration management, logging, lifecycle, DI, testing, Docker, and CI/CD. No domain logic or Gmail integration is implemented in this phase.

## Goals / Non-Goals

**Goals:**
- Establish a complete, navigable project structure following DDD + bounded context architecture
- Provide configuration via pydantic-settings with .env file support
- Enable structured JSON logging with sensitive data redaction
- Support async application lifecycle (startup/shutdown) for DB, OAuth, and event bus
- Provide a lightweight DI container without heavy framework dependencies
- Set up testing infrastructure with tiered coverage floors (≥90% Domain, ≥80% overall)
- Containerize with Docker and docker-compose for local development
- Automate lint, type-check, test, and security scanning via GitHub Actions

**Non-Goals:**
- Gmail API integration (Phase 5)
- Domain entities and business logic (Phases 3+)
- MCP tool implementations (Phase 7)
- Production deployment beyond Docker (Phase 8)
- Email filtering rules (out of scope for V1 per implementation plan)

## Decisions

1. **Hatchling as build system** — hatchling is the modern, standard Python build backend with native pyproject.toml support. Alternatives considered: setuptools (legacy, verbose), poetry (opinionated, lockfile overhead for a library).

2. **Pydantic-settings for configuration** — integrates naturally with pydantic models, supports .env files, environment variable prefixes, and validation out of the box. Alternatives considered: raw dotenv parsing (no validation), dynaconf (overweight for this scope).

3. **SQLite as default persistence** — zero-config, file-based, sufficient for local caching layer. PostgreSQL available via optional extras. This avoids requiring a database server for basic operation.

4. **Stdio transport as default MCP transport** — designed for AI agent consumption; simpler than HTTP, no port management. HTTP transport available as option.

5. **Lightweight DI container (dict-based)** — avoids framework lock-in (e.g., dependency-injector, fastapi.Depends). A simple dict with type-hinted resolve/factory methods suffices for this project's scope.

6. **pytest with asyncio_mode=auto** — avoids explicit @pytest.mark.asyncio decorators on every test. Alternatives considered: unittest (verbose, no native async), hypothesis (property-based, overkill here).

7. **Ruff for linting + mypy for type checking** — ruff replaces flake8/isort/black with a single fast tool; mypy provides static type checking. Alternatives considered: pyright (good but less ecosystem integration), black+isort separately (redundant with ruff).

8. **Tiered coverage floors** — Domain layer (≥90%) is business-critical and deserves higher coverage; overall floor (≥80%) allows infrastructure/boilerplate to have lower coverage without failing CI.

## Risks / Trade-offs

- [Over-engineering foundation] → Phase 1 defines structure for 4 bounded contexts upfront. Some directories may remain empty until later phases. Mitigation: stub files are minimal (__init__.py only); no premature implementation.
- [DI container too simple] → A dict-based resolver may not handle complex dependency graphs. Mitigation: if needed, the container can be replaced with a proper framework later; the interface is isolated.
- [Python 3.11+ requirement] → Excludes users on older Python versions. Mitigation: 3.11 is the minimum for modern type hints (TypeGuard, Self) and is widely available.
- [Lockfile management] → Lockfiles can drift. Mitigation: CI validates lockfile; hatchling or uv manages lockfile generation.
