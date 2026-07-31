# Backend Guidelines

> Load when implementing or modifying backend code.
>
> This document defines implementation standards for backend development.
> Architecture, testing, security, documentation, and Git workflows are defined in their respective guideline files.

---

# General Principles

Always:

- Prefer correctness over cleverness.
- Prefer explicitness over magic.
- Prefer readability over brevity.
- Make the smallest change that correctly solves the problem.
- Follow existing project conventions before introducing new patterns.

Avoid:

- unnecessary abstractions
- speculative design
- premature optimization
- unrelated refactoring

---

# Code Organization

Every file should have a single, well-defined responsibility.

Prefer small, cohesive modules over large, multi-purpose classes.

Avoid generic folders or generic names such as:

- Helper
- Utils
- Common
- Manager
- Processor
- Misc

Names should communicate business intent.

---

# Naming

Names should describe **what** something represents or **what** it does.

Examples

Use Cases

```
CreateInvoice
RegisterUser
CancelSubscription
```

Repositories

```
UserRepository
InvoiceRepository
```

Repository Implementations

```
PostgresUserRepository
RedisSessionRepository
```

Value Objects

```
Email
Money
Address
Currency
```

Domain Events

```
UserRegistered
InvoicePaid
SubscriptionCancelled
```

Prefer complete, descriptive names over abbreviations.

---

# Public APIs

Public interfaces should be:

- small
- explicit
- stable

Avoid exposing implementation details.

Accept and return explicit request and response models rather than persistence entities.

---

# Validation

Validate all external input at the system boundary.

Examples:

- HTTP requests
- CLI arguments
- events
- message queues
- uploaded files

Business validation belongs inside the business logic.

Examples

Boundary validation

- required fields
- data types
- format

Business validation

- email must be unique
- account must be active
- invoice must not already be paid

---

# Error Handling

Fail fast.

Raise meaningful, domain-specific errors whenever possible.

Good

```
UserAlreadyExists
InvalidCredentials
OrderNotFound
```

Avoid exposing infrastructure or framework exceptions outside their layer.

Translate technical failures at the application boundary.

Never silently ignore errors.

---

# Dependency Injection

Dependencies should be injected.

Avoid:

- service locators
- global state
- singleton access
- hidden dependencies

Components should explicitly declare everything they require.

---

# Configuration

Configuration belongs at the application's edge.

Never access:

- environment variables
- framework configuration
- secrets

directly from business logic.

Inject configuration through the appropriate layer.

---

# Persistence

Business logic should never depend on persistence technology.

Repositories expose business operations rather than database operations.

Prefer

```
findByEmail()
save()
exists()
```

Avoid

```
executeQuery()
executeSql()
```

outside infrastructure.

---

# External Systems

Access external systems through dedicated abstractions.

Examples

- PaymentGateway
- EmailSender
- FileStorage
- NotificationService

Business logic should not know implementation details.

---

# Logging

Log meaningful events rather than implementation steps.

Logs should provide enough context to answer:

- What happened?
- Which resource?
- Why?
- Correlation ID (when available)

Never log:

- passwords
- secrets
- tokens
- sensitive personal information

---

# Asynchronous Processing

Use asynchronous processing only when it provides a clear benefit.

Typical examples:

- email delivery
- notifications
- imports
- exports
- long-running jobs

Avoid asynchronous workflows for simple request-response operations.

---

# Transactions

Keep transactions:

- short
- explicit
- limited to a single business operation

Avoid long-running transactions.

---

# Performance

Correctness comes first.

Before optimizing:

1. Identify the bottleneck.
2. Measure it.
3. Optimize.
4. Measure again.

Avoid optimizing without evidence.

---

# Backwards Compatibility

Maintain backwards compatibility for public contracts unless explicitly instructed otherwise.

Breaking changes require:

- versioning
- migration strategy
- documentation updates

Examples of public contracts include:

- REST APIs
- GraphQL APIs
- Events
- SDKs

---

# Language

All technical artifacts must use English.

Including:

- source code
- identifiers
- comments
- documentation
- tests
- commit messages
- log messages
- error messages

---

# Related Guidelines

Load additional guideline files when relevant.

| Topic | File                                |
|--------|-------------------------------------|
| Architecture | `specs/docs/architecture.md`        |
| Testing | `specs/guidelines/testing.md`       |
| Security | `specs/guidelines/security.md`      |
| Documentation | `specs/guidelines/documentation.md` |
| Git Workflow | `specs/guidelines/git.md`           |
