---
name: finish-task
description: Mandatory completion checklist for any implementation task. Verify requirements, quality gates, documentation, and persist durable knowledge before considering work complete.
---

# Finish Task

Do not declare a task complete until every applicable gate below passes.

If a gate fails, fix it and repeat that gate before continuing.

---

## 1. Requirements

Verify the implementation satisfies every requested requirement.

- Confirm each requested behavior has been implemented.
- Identify any intentionally deferred work.
- Never assume passing tests imply complete implementation.

---

## 2. Testing

Verify the implementation through automated tests.

- Run the relevant test suite.
- New behavior must be covered by tests.
- Bug fixes must include a regression test whenever practical.
- Existing tests must continue to pass.

Report:

- executed command(s)
- test summary
- newly added or modified tests

---

## 3. Quality Checks

Run all applicable project quality checks.

Examples:

- formatter
- linter
- type checker
- static analysis

Report the result of each executed check.

---

## 4. Documentation

Determine which project documentation is affected.

Update every required document according to the project's documentation guidelines.

If no documentation changes are required, explicitly explain why.

---

## 5. Architecture Review

Verify the implementation respects the project's architectural principles.

Confirm that:

- responsibilities remain in the correct layer
- dependency direction is preserved
- no unnecessary abstractions were introduced
- existing project conventions were followed

If architectural deviations were necessary, explain them.

---

## 6. Change Hygiene

Review the final changeset.

Verify that it contains:

- no debug code
- no commented-out code
- no dead code
- no unrelated changes
- no secrets or sensitive information

If creating commits, follow the project's Git guidelines.

---

## 7. Project Memory

Persist only durable project knowledge.

Examples:

- architectural decisions
- implementation conventions
- recurring pitfalls
- long-term project constraints
- user preferences

Never save:

- temporary debugging
- implementation details
- task transcripts
- one-off fixes

If no durable knowledge was produced, explicitly state so.

---

## 8. Handoff Summary

Provide a concise summary including:

- what changed
- how it was verified
- documentation updated
- deferred work (if any)

---

# Failure Protocol

If any gate cannot pass:

- explain why
- provide evidence
- identify the impact
- never claim success without verification

---

# Anti-Patterns

Never:

- assume tests passed without running them
- assume requirements were met because code compiles
- save transcripts instead of distilled knowledge
- skip documentation without justification
- hide failing checks
