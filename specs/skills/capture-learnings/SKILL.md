---
name: capture-learnings
description: Turn corrections, failures, and discoveries into durable improvements. Use when the user corrects you, a command or approach fails unexpectedly, you repeat a mistake, or you discover a better way to do a recurring task. Use proactively at session end if any of these happened.
---
# Capture Learnings (self-improvement loop)

A correction absorbed only by the current context window is a correction you'll need again next week. This skill routes each learning to the ONE place where it becomes permanent.

## Triggers (be honest — these are easy to shrug off)
- The user corrects you ("no, we do X here", "actually…", "stop doing Y").
- The same command/approach failed twice, or failed for a non-obvious reason you eventually solved.
- You violated a guideline that exists but you missed — or needed a rule that doesn't exist.
- You discovered a faster/safer procedure for a recurring task.

## Workflow
1. **Distill** the learning into one falsifiable sentence: "<context>: <do/avoid X> because <consequence>". No narratives.
2. **Deduplicate**: search the memory MCP and grep `ai-specs/specs/` + `AGENTS.md` for it. Already recorded → stop (or sharpen the existing entry instead of adding a twin).
3. **Route to exactly one home** (most-specific wins):
   | Learning type | Destination | Example |
   |---|---|---|
   | Personal preference / context about the user | memory MCP only | "prefers squash merges; hates emoji in commits" |
   | Project-specific fact or quirk | project `AGENTS.md` (Project-specific quirks section) | "test container needs `TZ=UTC` or auth tests hang" |
   | Team/stack-wide rule that should bind every session | the matching `ai-specs/specs/*.md` file | "never hand-merge lockfiles" → git-workflow.md |
   | Requirement/behavior misunderstanding | `openspec/` — update the relevant spec or flag the gap in the active change's proposal | "sessions must survive password change" |
   | Reusable multi-step procedure | new or updated skill in `ai-specs/skills/` | "release tagging procedure" |
4. **Apply with consent tiers**: memory MCP + project AGENTS.md quirks → write directly, then report what you wrote. `ai-specs/specs/`, specs, or skills → propose the exact diff (file, line, before/after) and wait for approval; these bind future sessions and deserve a human gate.
5. **Always mirror to memory** (even when the primary home is a file) with a pointer: "guideline added to git-workflow.md re: lockfiles" — so recall works even before files are re-read.
6. **Report**: one line per learning — sentence, destination, applied/proposed.

## Quality bar for guideline additions
- One sentence, imperative, with the *why* ("because X breaks Y").
- Must be general enough to recur; one-off incidents belong in memory, not guidelines.
- Never grow a base guidelines file past its "small, always-injected" budget — if it's getting fat, the new rule belongs in a leaf file (testing/security/…) instead.

## Anti-patterns
- Apologizing and moving on → the failure repeats next session.
- Dumping a paragraph of prose into AGENTS.md → context tax forever; distill to one line.
- Recording the incident ("build failed on May 3") instead of the rule ("run codegen before build").
