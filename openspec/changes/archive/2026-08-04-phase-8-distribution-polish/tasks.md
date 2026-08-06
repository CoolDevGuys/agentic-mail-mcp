## 1. README (8.1)

- [x] 1.1 Expand `README.md`: project + architecture overview, pip and Docker installation, configuration pointer, stdio AI-agent integration example, contributing guidance
- [x] 1.2 Add the complete MCP tool catalog (read/write/intelligence/search) with one-line descriptions and the railguards security-model section (read-only default, allowlist, rate limits, archive-first, draft-first, audit log)

## 2. API reference (8.2)

- [x] 2.1 Create `specs/docs/api.md`: every MCP tool with name, description, input JSON-Schema, and output shape (source the tool set from the registry so it matches the code)
- [x] 2.2 Document the MCP resources (account/watch/index), prompts (search-strategy, email-management), and the structured error-response format from `MCP/errors.py`

## 3. Domain-model doc (8.3)

- [x] 3.1 Verify/complete `specs/docs/domain-model.md`: bounded-context overview, entity relationships, value-object catalog, domain-events catalog, aggregate boundaries — reconcile against the current code (add `EmailLabeled`, `AddLabelUseCase`, MCP layer if missing)

## 4. Configuration doc (8.4)

- [x] 4.1 Verify `specs/docs/configuration.md` documents every Settings field (gmail, database, railguards, mcp incl. `transport`, llm, notifications, logging, search) and is in sync with `.env.example`

## 5. Architecture ADRs (8.5)

- [x] 5.1 ADR `0002` — DDD + vertical slicing (bounded contexts over layered/technical folders)
- [x] 5.2 ADR `0003` — SQLite default / PostgreSQL optional persistence strategy
- [x] 5.3 ADR `0004` — Railguards write-safety model (read-only default, allowlist, rate limits, archive-first)
- [x] 5.4 ADR `0005` — MCP stdio transport as the default distribution mechanism; each ADR uses the Status/Context/Decision/Consequences template

## 6. PyPI packaging (8.6)

- [x] 6.1 Add a top-level `LICENSE` file (MIT) matching the `pyproject.toml` license
- [x] 6.2 Complete `pyproject.toml` distribution metadata: `readme = "README.md"`, `[project.urls]`, verify license/authors/classifiers/entry point
- [x] 6.3 Build the package (`python -m build` or `hatch build`) and confirm a valid sdist + wheel with the `gmail-mcp-server` entry point
- [x] 6.4 Document the Test-PyPI → production PyPI publish flow (in README or a release doc)

## 7. Docker multi-stage build (8.7)

- [x] 7.1 Rewrite the `Dockerfile` as multi-stage: builder stage builds a wheel; `python:3.11-slim` runtime installs only the wheel, runs as non-root, no build toolchain
- [x] 7.2 Wire a working health check (HTTP-transport mode) and confirm `docker-compose.yml` still starts the service (+ optional postgres)
- [x] 7.3 Document the multi-arch (`linux/amd64`, `linux/arm64`) `docker buildx` build and keep the Dockerfile architecture-agnostic

## 8. End-to-end tests (8.8)

- [x] 8.1 Add `tests/e2e/` driving the assembled MCP server through search → get → forward → archive → delete against a mocked Gmail API (read-write)
- [x] 8.2 Assert railguard enforcement E2E: write tools absent under read-only; a railguard denial returns a structured tool error under read-write
- [x] 8.3 Add a container startup + health-check smoke test, skipped when Docker is unavailable

## 9. Cleanup / release hygiene (8.9)

- [x] 9.1 Remove `token.json` and `credentials.json` from the repo; add them and the default token-storage path to `.gitignore`; flag that the exposed credential/token must be rotated and history-scrub is a separate follow-up
- [x] 9.2 Remove the superseded `main.py` and `server.py` skeletons (relocate to `examples/legacy/` only if they hold reference value)
- [x] 9.3 Final pass: `ruff check`, `mypy`, and the full test suite (unit + integration + e2e) all green; add a Phase 8 `CHANGELOG.md` entry
- [x] 9.4 `openspec validate phase-8-distribution-polish` passes
