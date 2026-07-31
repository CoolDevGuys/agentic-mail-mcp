---
name: finish-task
description: Mandatory closing checklist for any coding task. Use before declaring any feature, fix, or refactor done - verifies tests, docs, git hygiene, and persists session learnings to memory. Use proactively when about to say "done" or "complete".
---
# Finish a Task (Definition of Done gate)

You may not declare a task done until every gate below passes. Run them in order; report each with evidence (the actual command output), not assertion.

## Gates
1. **Tests** — run the FULL suite now. Paste the summary line. Any new behavior in this change must have a test that fails without it — name the test(s). Skipped/weakened tests = fail this gate.
2. **Static checks** — lint + type-check clean. Paste outputs.
3. **Docs (per documentation-guidelines.md)** — walk the change→doc mapping table: schema change ⇒ `data-models.md`; endpoint ⇒ OpenAPI; event ⇒ `events.md`; env var ⇒ `.env.example` + config doc; decision ⇒ ADR. For each: updated, or state "N/A because …". "Forgot" is not an option.
4. **Diff hygiene** — review `git diff`: no debug output, no commented-out code, no unrelated changes, no secrets. Commit message(s) follow `git-workflow.md`.
5. **Spec sync (OpenSpec projects)** — if `openspec/` exists and this work belongs to a change: `tasks.md` checkboxes updated *truthfully* (only tasks with passing proof get checked); spec deltas still match what was actually built (update them if implementation diverged — with a note why); `openspec validate` passes — paste its output. Remind the user to `/opsx:archive` after merge.
6. **Memory persistence** — save to the memory MCP (project-tagged), as *distilled decisions, not transcripts*:
   - decisions made and their why ("chose optimistic locking for Invoice because …")
   - gotchas discovered ("the test container needs X env var or hangs")
   - user preferences expressed this session ("prefers table-driven tests")
   - what was completed ("Billing: invoice PDF export shipped on branch feature/…")
   Skip only if the session genuinely produced nothing durable — say so explicitly.
7. **Handoff summary** — 3–6 lines: what changed, how it's proven, what docs moved, anything intentionally deferred (with ticket/TODO location).

## Failure protocol
If any gate fails: fix it and re-run that gate. If it *cannot* pass (e.g. flaky unrelated test), do not hide it — report the failure, why it's unrelated, and the evidence. Never claim green that isn't.

## Anti-patterns
- "Tests should pass" → run them.
- Saving a session transcript to memory → save decisions only.
- Marking docs N/A without stating why.
