# AI Agent Instructions

This document is the entry point for AI coding assistants working in this repository.

Follow these instructions for every task. Load additional guidance progressively as needed.

---

# Workflow

Every task follows this workflow.

## 1. Research

Before making changes:

- Understand the user's request.
- Inspect the existing implementation.
- Determine the affected components.
- Identify project constraints.
- Load only the relevant guideline files.

Do **not** start implementing until you understand the problem.

---

## 2. Plan

For non-trivial tasks, create a concise implementation plan.

Include:

- affected files
- implementation approach
- tests to add or modify
- documentation to update

Ask for clarification before proceeding if:

- requirements are ambiguous
- multiple valid implementations exist
- the change is destructive or affects public contracts

Small, obvious tasks may skip this phase.

---

## 3. Implement

Implement the planned solution.

Rules:

- Make the smallest correct change.
- Preserve existing architecture and conventions.
- Avoid unrelated refactoring.
- Remove dead code instead of leaving it commented out.
- Reuse existing patterns whenever appropriate.

---

## 4. Verify

Before considering the task complete:

- verify the implementation satisfies the original request
- run formatting if available
- run linting if available
- run type checking if available
- run relevant tests

If verification cannot be completed, clearly explain why.

---

# Memory

## At Session Start

Search project memory using:

- project name
- current task

Use relevant memories to preserve previous architectural decisions, conventions, and user preferences.

---

## Task Classification

Determine the task type before planning.

- Bug Fix
- Feature
- Refactor
- Documentation
- Investigation
- Performance
- Security
- Infrastructure

Use the task type to determine which guideline files should be loaded.

---

## Before Finishing

Save only durable project knowledge such as:

- architectural decisions
- implementation conventions
- recurring pitfalls
- long-term user preferences
- important project constraints

Do **not** save temporary implementation details, debugging information, or one-off tasks.

---

# Progressive Disclosure

Load additional files only when they are relevant to the current task.

| Topic | File                                |
|--------|-------------------------------------|
| Project overview | `specs/docs/project.md`             |
| Architecture and project organization | `specs/docs/architecture.md`        |
| Backend implementation | `specs/guidelines/backend.md`       |
| Testing | `specs/guidelines/testing.md`       |
| Security | `specs/guidelines/security.md`      |
| Documentation | `specs/guidelines/documentation.md` |
| Git workflow | `specs/guidelines/git.md`           |

Never load unnecessary files.

---

# General Rules

Always:

- Understand before implementing.
- Prefer simple solutions.
- Follow existing project conventions.
- Keep changes cohesive.
- Preserve backwards compatibility unless explicitly requested otherwise.
- Write all code, documentation, comments, commit messages, logs, and identifiers in English.

Never:

- invent requirements
- change unrelated code
- bypass tests
- disable security checks for convenience
- commit secrets
- silently ignore errors

If something outside the requested scope appears incorrect, mention it instead of changing it automatically.

---

# Completion Checklist

Before finishing a task, verify that:

- the requested change has been fully implemented
- relevant project guidelines were followed
- tests were added or updated when appropriate
- documentation was updated when required
- verification steps completed successfully
- no unrelated files were modified
- durable knowledge has been saved to project memory when appropriate
