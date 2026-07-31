# Testing Guidelines

> Load when implementing features, fixing bugs, refactoring, or modifying existing behavior.
>
> Tests are the executable specification of the system.
> A task is not complete until the tests demonstrate the expected behavior.

---

# Goal

The objective of testing is to prove that the requested behavior works correctly and continues to work as the code evolves.

Tests should give confidence that:

- the implementation satisfies the requirements
- existing behavior has not been broken
- future refactoring remains safe

Tests should verify behavior, never implementation details.

---

# Testing Workflow

Every implementation follows this cycle.

```
Understand Requirement

↓

Define Expected Behavior

↓

Write or Update Tests

↓

Implement

↓

Run Tests

↓

Fix

↓

Repeat until all tests pass
```

Do not consider the task complete until the implementation and the tests agree.

---

# General Principles

Always:

- Test behavior through public interfaces.
- Keep tests deterministic.
- Keep tests independent.
- Make tests easy to understand.
- Write one assertion purpose per test.
- Prefer a few meaningful tests over many shallow ones.

Avoid:

- testing implementation details
- duplicating implementation logic inside tests
- relying on execution order
- relying on real time
- relying on external services
- unnecessary mocking

---

# Test First Mindset

When implementing new behavior:

1. Understand the expected behavior.
2. Create or update the corresponding tests.
3. Implement the feature.
4. Verify the tests pass.

When fixing bugs:

1. Reproduce the bug with a failing regression test.
2. Fix the implementation.
3. Verify the regression test passes.
4. Verify no existing behavior broke.

Never fix a bug without first capturing it in a test unless technically impossible.

---

# Test Pyramid

Prefer the following distribution.

## Unit Tests

Majority of tests.

Verify:

- business rules
- calculations
- validation
- domain behavior

Unit tests should:

- execute quickly
- have no external dependencies
- require no infrastructure

---

## Integration Tests

Verify interaction between components.

Examples:

- database
- messaging
- persistence
- HTTP layer
- external adapters

Use real infrastructure whenever practical.

---

## End-to-End Tests

Only for critical user journeys.

Examples:

- authentication
- checkout
- registration
- payment

Avoid excessive end-to-end testing.

---

# Test Design

Every test should answer one question.

Example

```
Should reject expired access token.
```

Not

```
Authentication test.
```

Good test names describe expected behavior.

Examples

```
creates_invoice_when_payment_succeeds

rejects_duplicate_email

returns_404_for_unknown_user
```

---

# Assertions

Every assertion should verify observable behavior.

Prefer assertions about:

- returned values
- state changes
- published events
- persisted data
- visible responses

Avoid asserting:

- internal variables
- private methods
- call order (unless behavior depends on it)

---

# Determinism

Tests must always produce the same result.

Never depend on:

- current time
- randomness
- execution order
- network latency
- external APIs

Inject or control these dependencies.

---

# Test Data

Create only the data required for the test.

Prefer:

- builders
- fixtures
- factories

Avoid:

- massive shared fixtures
- unnecessary setup
- copy-pasted data

Every piece of test data should help explain the scenario.

---

# Mocking

Prefer real implementations whenever practical.

Order of preference:

1. Real implementation
2. In-memory fake
3. Stub
4. Mock

Mock only true external dependencies.

Examples:

- payment gateways
- email providers
- cloud storage
- third-party APIs

Do not mock your own business logic.

---

# Coverage

Coverage is an indicator, not a goal.

High coverage with weak assertions provides little value.

Prioritize:

- meaningful assertions
- critical business rules
- edge cases
- error paths

over percentages.

---

# Regression Protection

Every bug fix should permanently prevent the same bug.

Workflow

```
Bug discovered

↓

Regression test added

↓

Bug fixed

↓

Regression test passes
```

The regression test should fail without the fix.

---

# Edge Cases

Consider whether the implementation should be tested for:

- invalid input
- missing input
- empty collections
- boundary values
- duplicate operations
- concurrency
- authorization
- error handling

Do not add meaningless edge-case tests.

Test only behavior that matters.

---

# Refactoring Safety

If a refactor changes behavior unexpectedly,

the tests should fail.

Good tests allow internal implementation to change freely while protecting externally observable behavior.

---

# Verification Loop

Before completing any implementation, verify:

□ The original requirement is covered by one or more tests.

□ Every new behavior has at least one positive-path test.

□ Every important failure mode has at least one negative-path test.

□ Existing tests continue to pass.

□ The implementation is not tested through private methods.

□ Tests remain deterministic.

If any answer is "No",

the task is not complete.

---

# Test Adequacy Review

Before completing the task, evaluate the test suite as if the implementation had been written by someone else.

Ask:

- Can these tests detect an incorrect implementation?
- Could a trivial or incomplete implementation still pass?
- Are the most important business rules verified?
- Are error paths exercised?
- Are the assertions specific enough to catch regressions?

If weaknesses are found:

1. Improve the tests.
2. Re-run the test suite.
3. Repeat this review.

The implementation is complete only when the tests provide high confidence that the requested behavior is correct.

---

# Related Guidelines

| Topic | File                                |
|--------|-------------------------------------|
| Project Architecture | `specs/docs/architecture.md`        |
| Backend Development | `specs/guidelines/backend.md`       |
| Security | `specs/guidelines/security.md`      |
| Documentation | `specs/guidelines/documentation.md` |
