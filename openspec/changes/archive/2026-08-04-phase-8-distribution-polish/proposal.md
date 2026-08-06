## Why

Phases 1–7 delivered a complete, tested Gmail MCP server, but it is **not yet shippable**: there is no `LICENSE`, no MCP tool/resource reference (`specs/docs/api.md`), only one of the four planned architecture ADRs, a minimal single-stage Dockerfile, no end-to-end tests, and the repo still carries pre-DDD skeletons (`main.py`, `server.py`) and — critically — committed secrets (`token.json`, `credentials.json`). Phase 8 is the distribution-and-polish pass that makes the project publishable to PyPI and Docker, fully documented, and clean.

## What Changes

- **Documentation set**: complete the `README.md` (install via pip/docker, full configuration, the complete tool catalog, the railguards security model, usage/integration examples, contributing); add `specs/docs/api.md` (every MCP tool/resource/prompt with input/output schemas and error formats); verify `specs/docs/domain-model.md` and `specs/docs/configuration.md` are complete and in sync with the code.
- **Architecture ADRs**: add the four decision records the plan calls for — DDD + vertical slicing, SQLite-default/PostgreSQL-optional persistence, the railguards write-safety model, and MCP stdio as the default transport — each following the documentation-standards ADR template.
- **PyPI packaging**: add a `LICENSE` file (MIT, matching the declared metadata) and complete `pyproject.toml` for distribution (`readme`, `project.urls`, verified build); produce a valid sdist + wheel with the `agentic-mail-mcp` console entry point; document the Test-PyPI → PyPI publish flow.
- **Docker multi-stage build** (**BREAKING** for the current image shape): replace the single-stage Dockerfile with a builder stage (install/build) + slim runtime stage (copy built package), non-root user, a working health check, and multi-arch (amd64/arm64) build support.
- **End-to-end tests**: a full MCP-session test suite exercising tool flows (search → read → forward → archive → delete) and railguard enforcement against a mocked Gmail API, plus a container startup/health-check smoke test.
- **Cleanup / release hygiene**: remove the superseded `main.py` and `server.py` skeletons (relocate to `examples/legacy/` if retained), remove `token.json`/`credentials.json` from the repo and add them (and the default token-storage path) to `.gitignore`, and run a final lint + type-check + full-suite pass.

## Capabilities

### New Capabilities
- `distribution-docs`: the release documentation set — a complete README (install, configuration, tool catalog, railguards model, usage), `specs/docs/api.md` (MCP tool/resource/prompt reference with schemas and error formats), a complete domain-model catalog, and the four architecture ADRs.
- `pypi-packaging`: a buildable, publishable distribution — a `LICENSE` file, complete `pyproject.toml` metadata, a valid sdist + wheel exposing the `agentic-mail-mcp` entry point, and a documented Test-PyPI → PyPI publish flow, with the repository free of committed secrets and superseded skeletons.
- `e2e-tests`: end-to-end MCP-session tests covering the read/write tool flow and railguard enforcement against a mocked Gmail API, plus a Docker container startup and health-check smoke test.

### Modified Capabilities
- `docker`: the image becomes a multi-stage build (builder + slim runtime), keeps the non-root user and health check, and gains multi-arch (amd64/arm64) support.

## Impact

- New files: `LICENSE`, `specs/docs/api.md`, `specs/docs/adr/0002…0005-*.md`; expanded `README.md`; new `tests/e2e/` suite; optional `examples/legacy/`.
- Modified: `Dockerfile` (multi-stage, health check, multi-arch), `pyproject.toml` (`readme`, `project.urls`), `.gitignore` (ignore `token.json`, `credentials.json`, and the default token-storage path), `CHANGELOG.md`.
- Removed from the repo: `token.json`, `credentials.json` (secrets — **security fix**), `main.py`, `server.py` (superseded skeletons). The existing ADR `0001-shared-primitives.md` is retained; the four new architectural ADRs are numbered `0002`–`0005` to avoid renumbering it.
- No application/behavior code changes: Phase 8 is documentation, packaging, containerization, tests, and cleanup. Depends on the finished Phase 1–7 code (MCP server, tools, railguards) being stable; no new runtime dependencies beyond dev/test tooling already declared (`pytest-httpserver`).
