---
name: review-pr
description: Review a diff, branch, or pull request against the project's standards. Use when the user asks to review code, check a PR, or as the final gate before merge. Read-only review - never fixes code.
---
# Review a PR / Diff

You report findings; you never edit. Ground every finding in the actual diff and cite `file:line`.

## Workflow
1. **Load context** — get the diff (`git diff main...HEAD` or the provided range) and the list of changed files. Read the intent artifacts: in OpenSpec projects, the active `openspec/changes/<name>/` (proposal.md, spec deltas, design.md, tasks.md); otherwise `docs/plans/*.md` if present. The review is against *intent*, not just style.
2. **Load the applicable rules** — `ai-specs/specs/backend-standards.md` and/or `frontend-standards.md`, plus `testing-standards.md`, plus `security-guidelines.md` if the diff touches auth/input/secrets/data exposure, plus the framework guideline for this stack. Review against these files, not personal taste.
3. **Recall** — query memory MCP for prior decisions relevant to the touched contexts; flag contradictions with recorded decisions.
4. **Review passes** (in order, report per pass):
   - **Intent conformance** (when intent artifacts exist): does the diff do what the proposal/spec deltas say — all of it, and nothing beyond it? Unimplemented spec scenario = blocker; unproposed behavior change = blocker (scope creep); checked-off task without its proof = blocker.
   - **Correctness**: logic errors, unhandled edge cases, race conditions, broken contracts.
   - **Architecture**: dependency-rule violations (Domain importing Infrastructure = blocker), wrong layer/context placement, forbidden naming (`*Service` suffix), context leakage.
   - **Tests**: does every new behavior have a test that would fail without the change? Are tests asserting behavior, not implementation? Any test deleted/skipped/weakened? (blocker).
   - **Security**: per security-guidelines — injection, missing authz, secret exposure, mass-exposure DTOs.
   - **Docs (Definition of Done)**: schema change without `data-models.md` update, endpoint without OpenAPI update, missing changelog → blocker per base guidelines.
   - **Diff hygiene**: unrelated changes, dead/commented code, debug leftovers.
5. **Severity-tag every finding**: `[BLOCKER]` must fix before merge · `[SHOULD]` fix now or ticket it · `[NIT]` optional.

## Output contract
```
Verdict: APPROVE | APPROVE WITH NITS | REQUEST CHANGES
Blockers: n · Should: n · Nits: n

[BLOCKER] src/Billing/Domain/Invoice.php:42 — imports Doctrine (violates
dependency rule, base-backend-guidelines §Architecture). Suggestion: <1 line>.
...
Positive: <1–2 things done well — reinforces good patterns>
```
Verdict rule: any `[BLOCKER]` ⇒ REQUEST CHANGES. No blockers ⇒ APPROVE (WITH NITS if any). Never soften a blocker into a "should" to be polite.

## Anti-patterns
- Reviewing style the linter already enforces → skip, tools own that.
- "Consider maybe possibly…" hedging → state the rule violated and the fix.
- Praising to fill space → one honest positive max.
