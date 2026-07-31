---
name: resolve-merge-conflict
description: Safely resolve git merge or rebase conflicts. Use when a merge/rebase reports conflicts, the user mentions conflict markers, or a branch needs updating against main.
---
# Resolve Merge Conflicts

Golden rule: a conflict is two *intents* colliding, not two texts. Resolve intents; the proof is the test suite.

## Workflow
1. **Map the situation** — `git status` for conflicted files; `git log --oneline main..HEAD` and `HEAD..main` to understand what each side was doing. State in one sentence per side: "ours = X, theirs = Y".
2. **Recall intent** — read the plan/commits behind *our* branch; query memory MCP for decisions about the touched files ("did we deliberately change this behavior?"). If both sides changed the same behavior *on purpose*, that's a product decision — stop and ask, don't pick silently.
3. **Resolve file by file**, smallest first:
   - Read the whole conflicted file, not just the markers — conflicts often need surrounding-code adjustments (renamed vars, moved imports).
   - Prefer **semantic union**: keep both features when independent; keep the newer contract when one side is a refactor of the same logic.
   - Special cases: lockfiles → regenerate (`pnpm install` / `composer update --lock`), never hand-merge. Generated files → regenerate from source. Migrations → never merge two into one; re-sequence ours after theirs.
4. **Gate: no conflict markers remain** — `git grep -nE '^(<<<<<<<|=======|>>>>>>>)'` must return empty before continuing.
5. **Gate: full verification** — build/type-check, lint, **entire test suite** (not just touched-file tests — conflicts break at a distance). A resolution without a green suite is not a resolution.
6. **Commit** — complete the merge/rebase with a message listing each conflicted file and the one-line rationale for its resolution.

## Output contract
Report: files resolved + strategy per file (ours/theirs/union/regenerated), test-suite result, and any behavior decision you made or deferred to the user.

## Anti-patterns
- Accepting `--ours`/`--theirs` wholesale to make errors go away → silent feature deletion.
- Resolving markers top-to-bottom without reading the file → compiles, but Frankenstein logic.
- Skipping the full suite because "the conflict was small" → the classic post-merge production bug.
