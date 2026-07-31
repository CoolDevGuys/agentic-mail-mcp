# Git Workflow

> Load before branching, committing, or opening a PR.

## Branching
- Never commit directly to `main`. Every change goes through a **feature branch** (or a git worktree of one for parallel agent work).
- Branch naming: `<type>/<ticket-or-context>-<short-kebab-description>`
  - Types: `feature/`, `fix/`, `refactor/`, `chore/`, `docs/`, `hotfix/`
  - Examples: `feature/BIL-142-invoice-pdf-export`, `fix/identity-token-expiry`
- Keep branches short-lived (< a few days). Rebase on `main` before opening/updating a PR.

## Worktrees (recommended for AI agents)
Run each agent task in its own worktree so parallel sessions never collide:
```bash
git worktree add ../repo-feature-x feature/BIL-142-invoice-pdf-export
# work there; remove when merged:
git worktree remove ../repo-feature-x
```

## Commits
- Conventional Commits: `<type>(<scope>): <imperative summary ≤ 72 chars>`
  - `feat(billing): add PDF export for invoices`
  - `fix(identity): reject expired refresh tokens`
- One logical change per commit; tests and their implementation commit together.
- Never commit: secrets, `.env`, generated artifacts, commented-out code, unrelated formatting churn.

## Pull requests
- PR description: what + why, how it was tested, and which docs were updated (or why none needed).
- CI must be green (lint, types, tests) before merge. Squash-merge unless the project says otherwise.
