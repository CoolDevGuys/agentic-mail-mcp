# Documentation Guidelines

## General rules
- ALWAYS WRITE IN ENGLISH, including comments and any explanation in the files. This applies both to creating new documentation and updating existing one, and it also applies to documentation within the code (comments, explanations of functions or fields, etc.).

> Load before closing any task. Documentation is part of Definition of Done.

## The rule
Every change updates the documentation that describes what changed — in the same branch/PR. If nothing needs updating, state that explicitly in the PR description.

## Change → document mapping
| Change | Update                                                                             |
|---|------------------------------------------------------------------------------------|
| Behavior/requirement change (OpenSpec projects) | spec delta in the active `openspec/changes/<name>/specs/`; merged to `openspec/specs/` via archive after merge |
| New/modified DB table, column, relation | `specs/docs/data-model.md` — model definition, fields, relations, indexes       |
| New/modified API endpoint | OpenAPI file (`specs/docs/api-spec.yaml`) — path, schemas, error responses, auth |
| New domain event | `specs/docs/events.md` — name, payload schema, producers, consumers                    |
| New env var / config key | `.env.example` + `specs/docs/configuration.md`                                         |
| New bounded context or architectural decision | `specs/docs/adr/NNNN-title.md` (ADR, see below)                                        |
| New shared UI component | Component doc/story — props, variants, usage example                               |
| Behavior change affecting users/operators | `CHANGELOG.md` entry                                                               |

Split of ownership in OpenSpec projects: **specs own behavior** (requirements, scenarios); `specs/docs/data-model.md`/OpenAPI own technical contracts. Don't duplicate a fact in both — pick the owner.

## Style
- Write for the reader who arrives with zero context. Short sentences, concrete examples.
- Documents live next to the code in the repo (`specs/docs/`), versioned with it.
- Keep each doc current, not historical — history lives in git, decisions live in ADRs.

## ADRs (Architecture Decision Records)
For decisions with lasting consequences (new dependency, pattern change, context boundary). Template — keep it under one page:
```
# NNNN — Title
Status: accepted | superseded by NNNN
Context: what forced a decision
Decision: what we chose
Consequences: what becomes easier/harder
```
