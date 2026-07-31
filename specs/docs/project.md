# Project Overview

> This document provides the high-level context for the project.
> It describes **what** the project is and **why** it exists.
> Implementation details and engineering standards are documented elsewhere.

---

# Purpose

Gmail MCP Server is a Model Context Protocol (MCP) server that exposes Gmail operations for AI agents. It provides a structured, safe interface for AI agents to read, search, summarize, and manage email through a standardized protocol, with built-in safety controls (railguards) that prevent unauthorized or destructive actions.

The server bridges the gap between AI agent tooling and Gmail's API, offering capabilities across four bounded contexts: Gmail operations, AI-powered intelligence (summarization, classification, suggestions), semantic search, and real-time notifications.

---

# Goals

- Provide AI agents with a standardized, protocol-compliant interface to Gmail
- Enable safe email operations with read-only-by-default access and configurable railguards
- Offer AI-powered email intelligence: summarization, classification, reply suggestions, action item extraction
- Support semantic search over email content via embedding-based vector search
- Deliver real-time inbox notifications through configurable channels (webhooks, Redis)
- Default to a lightweight, zero-infrastructure deployment (SQLite, stdio transport)
- Distribute as both a PyPI package and a Docker image

---

# Non-Goals

- This is not a full Gmail client or webmail replacement
- Server-side Gmail auto-filters (creating/managing persistent filter rules) are out of scope for V1
- Real-time chat or messaging beyond email is not supported
- Multi-account management; the server operates against a single Gmail account
- Native mobile applications or browser extensions

---

# Technology Stack

Backend:

- Python 3.11+
- MCP SDK (mcp)
- Pydantic / Pydantic Settings
- SQLAlchemy (async)
- httpx (HTTP client)
- google-api-python-client / google-auth-oauthlib

Frontend:

- None (server-only, consumed by AI agents via MCP protocol)

Database:

- SQLite (default, via aiosqlite)
- PostgreSQL (optional, via asyncpg + psycopg2)
- Alembic for migrations

Infrastructure:

- Docker / Docker Compose
- GitHub Actions (CI/CD)
- PyPI (package distribution)

---

# External Systems

- **Gmail API** — core email operations (read, search, send, label, archive, delete)
- **OAuth 2.0** — authentication and token management for Gmail API access
- **LLM Providers** — AI intelligence features (llama.cpp local models or OpenAI-compatible APIs)
- **Embedding Models** — BGE for text vectorization (semantic search)
- **Notification Channels** — webhooks (HTTP POST), Redis (pub/sub), RabbitMQ (message queue)

---

# Constraints

- **Read-only by default** — write operations require explicit `read_write` access level in railguard configuration
- **OAuth tokens stored outside the repository** and encrypted at rest; never logged or committed
- **Draft-first sending** — all outbound email goes through a draft for human review before sending
- **Structured logging with redaction** — sensitive data (tokens, passwords, email bodies) is masked in logs
- **SQLite default** — the project must work out of the box with a single-file database; PostgreSQL is optional
- **Python 3.11+** — minimum runtime requirement

---

# Success Criteria

The project is considered successful when it consistently delivers:

- Correct functionality
- Maintainable code
- Reliable automated tests
- Up-to-date documentation
- Predictable development workflows
