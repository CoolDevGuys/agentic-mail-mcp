# Architecture

> This document defines the architectural principles of the project.
> It describes **how the system is organized**, not how individual components are implemented.

---

# Architectural Style

The project follows these principles:

- Domain-Driven Design (DDD)
- Hexagonal Architecture (Ports & Adapters)
- Vertical Slice Architecture
- Screaming Architecture

The goal is to organize the code around business capabilities rather than technical concerns.

---

# Project Structure

Top-level directories represent **bounded contexts**, not technical layers.

Example:

```text
src/

    Billing/

        Application/

        Domain/

        Infrastructure/

    Identity/

        Application/

        Domain/

        Infrastructure/

    Shared/
```

Each bounded context owns its business logic and implementation.

Avoid generic folders such as:

- services
- helpers
- utils
- common
- misc

Folder names should communicate business intent.

---

# Layers

Each bounded context is organized into three primary layers.

## Domain

Contains business knowledge.

Examples:

- Entities
- Value Objects
- Domain Events
- Repository Interfaces
- Domain Services (only when necessary)

The Domain layer:

- contains no framework code
- contains no infrastructure code
- has no external dependencies

---

## Application

Coordinates business use cases.

Examples:

- Commands
- Queries
- Use Cases
- Handlers
- DTOs

The Application layer:

- orchestrates business operations
- depends only on the Domain layer
- contains no infrastructure concerns

---

## Infrastructure

Implements technical concerns.

Examples:

- HTTP Controllers
- Database Repositories
- ORM Models
- External API Clients
- Message Brokers
- File Storage

Infrastructure depends on Application and Domain.

Business rules never belong here.

---

# Dependency Rule

Dependencies always point inward.

```text
Infrastructure
        ↓
Application
        ↓
Domain
```

The Domain layer must never depend on:

- frameworks
- databases
- HTTP
- messaging
- configuration
- infrastructure

Violations of this rule are architectural defects.

---

# Bounded Contexts

Each bounded context owns:

- its business rules
- its persistence
- its application services
- its events

Avoid sharing business logic between contexts.

When two contexts need similar behavior, first determine whether the concepts are actually the same.

---

# Communication

Bounded contexts communicate through:

- application interfaces
- domain events

Never access another context's internal implementation directly.

Avoid importing another context's Domain objects.

---

# Shared Code

The `Shared` module should remain small.

Appropriate examples include:

- shared abstractions
- cross-cutting primitives
- common infrastructure

Do not place business logic inside `Shared`.

When business logic becomes shared, reconsider the bounded context boundaries instead.

---

# Configuration

Configuration belongs at the application's edge.

Business logic must not read:

- environment variables
- configuration files
- framework configuration

Configuration should be injected through the appropriate layer.

---

# External Dependencies

External systems are accessed only through abstractions.

Examples:

- payment providers
- email providers
- storage services
- messaging systems

Business logic should depend on interfaces, not implementations.

---

# Evolution

Architecture should evolve incrementally.

Prefer:

- small architectural improvements
- incremental refactoring
- preserving consistency

Avoid:

- unnecessary rewrites
- speculative abstractions
- introducing new patterns without clear benefit

Consistency across the codebase is more valuable than adopting the newest architectural trend.
