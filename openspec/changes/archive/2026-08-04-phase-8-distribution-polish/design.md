## Context

The application is feature-complete and green (Phases 1–7): the MCP server, its read/write/intelligence/search tools, resources, prompts, the railguards framework, and all infrastructure adapters exist and are tested. What remains is everything around the code needed to ship it. Today: `README.md` is a 139-line stub missing the tool catalog and usage; `specs/docs/api.md` does not exist; `specs/docs/domain-model.md` (404 lines) and `specs/docs/configuration.md` already exist and are current; only `specs/docs/adr/0001-shared-primitives.md` exists; the `Dockerfile` is a minimal single-stage image; there are no end-to-end tests; and `main.py`, `server.py`, `token.json`, and `credentials.json` are still committed at the repo root. `pyproject.toml` already declares `license = "MIT"` and classifiers but has no `LICENSE` file, no `readme`, and no `project.urls`.

## Goals / Non-Goals

**Goals:**
- Make the package installable and publishable (pip / PyPI) and runnable as a container image, with a license.
- Give an integrator everything they need from docs alone: how to install, configure, which tools exist, and how the safety model works.
- Prove the whole system end-to-end with a mocked Gmail API, including railguard enforcement.
- Remove committed secrets and dead skeletons; leave a clean, releasable tree.

**Non-Goals:**
- Any application behavior change — no new tools, use cases, or runtime code. (Doc/test/packaging only.)
- Actually pushing to production PyPI or a registry in this change — we make it buildable and document the flow; the human runs the publish.
- New bounded contexts, ADRs beyond the four listed, or V2 features (e.g. Gmail filter rules, per the scope note).
- PostgreSQL/pgvector/model-weight paths in E2E — those stay in guarded integration tests.

## Decisions

**1. Documentation split follows documentation-standards ownership.**
Specs own behavior; `specs/docs/*` own technical contracts. So `specs/docs/api.md` is the MCP surface reference (tool names, JSON-Schema inputs, output shapes, the structured error format from `MCP/errors.py`), `domain-model.md` owns the entity/event catalog, `configuration.md` owns the settings matrix, and `README.md` is the entry point that links out. No fact is duplicated across two docs — the README points to the others rather than restating them.

**2. Keep ADR `0001-shared-primitives.md`; add the four architectural ADRs as `0002`–`0005`.**
The plan lists ADR topics as "0001–0004", but `0001` is already taken by a real, merged ADR. Renumbering an accepted ADR would break references, so the four new ones become `0002` (DDD + vertical slicing), `0003` (SQLite-default / PostgreSQL-optional), `0004` (railguards write-safety model), `0005` (MCP stdio default transport). Each uses the Status/Context/Decision/Consequences template.

**3. Multi-stage Dockerfile: build a wheel in the builder, install it in a slim runtime.**
The builder stage installs build deps and produces a wheel; the runtime stage is `python:3.11-slim`, copies and installs only the wheel, runs as a non-root user, and keeps the health check. This shrinks the image and removes build toolchain from the runtime. Multi-arch (amd64/arm64) is expressed via `docker buildx` documented in the README — the Dockerfile itself stays arch-agnostic. This modifies the existing `docker` capability (base image, non-root, health check, compose services all stay; the staging and multi-arch requirements are added/strengthened).

**4. Health check probes the MCP port only when HTTP transport is enabled.**
stdio is the default transport and has no port to probe. The container health check targets the HTTP transport (the deployment mode where a container is actually useful); the README documents that the health check assumes `AGENTIC_MAIL_MCP_MCP_TRANSPORT=http`. This keeps the existing `docker` "Health check" requirement satisfiable rather than aspirational.

**5. E2E tests drive the real `MCPServer` with a mocked Gmail transport.**
The E2E suite builds the server via `create_server` with an `McpUseCases` bundle wired to the real use cases but a mocked Gmail API (`pytest-httpserver`, already a dev dep, or the existing gateway fakes at the seam), then calls tools through the server's `call_tool` and asserts the flow: search → get → forward/archive/delete, plus that write tools are absent/denied under `read_only`. A separate, optionally-skipped test builds the image and asserts the container starts and its health check passes. This becomes the new `e2e-tests` capability; unit/integration coverage floors are unchanged.

**6. Secret removal is a security fix, done carefully.**
`token.json` and `credentials.json` are removed from the working tree and added to `.gitignore` alongside the default token-storage path. The proposal flags that these were committed; purging them from **git history** is called out as a follow-up the human must decide on (history rewrite is out of scope for an automated change), but they are removed going forward and can no longer be re-added.

**7. `main.py` / `server.py` are deleted, not archived, unless they hold reference value.**
Both are superseded by `MCP/Server.py` + `Bootstrap/cli.py`. Default is removal; if either contains a useful usage example it moves to `examples/legacy/`. The `agentic-mail-mcp` entry point is already the real one, so nothing depends on them.

## Risks / Trade-offs

- **Committed secrets remain in git history** → Removing files going forward does not scrub history. Mitigation: flag prominently; recommend the human rotate the exposed Google credential/token and, if needed, run a history purge (BFG/filter-repo) as a separate operation. Rotation is the real fix — history rewrite alone doesn't un-expose a leaked secret.
- **Container health check depends on HTTP transport** → With the stdio default there is nothing to probe. Mitigation: document that the health check applies to HTTP-mode deployments; a stdio container is a foreground process whose liveness is the process itself.
- **E2E image/health test needs Docker in CI** → Not all CI runners have it. Mitigation: mark the container test with a marker and skip when Docker is unavailable, so the suite stays green locally and in minimal CI.
- **Docs drift from code** → A tool list in `api.md` can fall behind. Mitigation: generate/verify the tool list against the registry in a test where cheap, and keep `api.md` the single source so README doesn't duplicate it.
- **Multi-arch build cost** → arm64 emulation is slow in CI. Mitigation: multi-arch is a documented `buildx` command for release, not a per-PR CI gate.

## Migration Plan

Additive and subtractive, no behavior change. Land docs first (README, api.md, ADRs, verify domain-model/configuration), then the LICENSE + packaging metadata and a local build check, then the multi-stage Dockerfile, then the E2E suite, then cleanup (remove secrets + skeletons, update `.gitignore`), and finish with the final lint/type/test pass and CHANGELOG entry. Rollback is reverting the change; the removed skeletons and secrets are recoverable from history if ever needed (secrets should be rotated regardless). Publishing to PyPI and pushing the image are human-run release steps performed after this change merges.

## Open Questions

- Delete `main.py`/`server.py` outright, or relocate to `examples/legacy/`? Leaning delete unless review flags reference value.
- Should the four ADRs use `0002`–`0005` (keeps existing `0001`) or renumber to match the plan's `0001`–`0004`? Leaning keep existing `0001`, add `0002`–`0005`.
- Does the `docker` capability's health-check requirement need rewording to acknowledge the stdio/HTTP distinction, or is documenting the HTTP-mode assumption enough? Leaning document-only, no spec reword.
