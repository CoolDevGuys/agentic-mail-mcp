"""Interactive `init` wizard that generates a ``.env`` configuration file.

The wizard logic is kept pure and testable: it operates over an injected
``prompt`` callable and ``out`` stream rather than calling ``input()`` /
``print()`` directly, so tests can script answers (including invalid-then-valid
re-prompts) and assert on the written file without a real terminal.

The field table below is the single source of prompts. It mirrors
``.env.example`` (the reference of record) key-for-key and section order; a
drift-guard test asserts every ``AGENTIC_MAIL_MCP_`` key in ``.env.example`` is
produced here.
"""

from __future__ import annotations

import json
import os
import secrets
import shutil
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from agentic_mail_mcp.Bootstrap.Settings import Settings


@dataclass(frozen=True)
class Field:
    """One prompted configuration field."""

    key: str
    label: str
    default: str
    kind: str = "str"  # str|int|bool|choice|list|dict|path|secret_gen
    choices: tuple[str, ...] = ()


@dataclass(frozen=True)
class Section:
    name: str
    fields: list[Field] = field(default_factory=list)


# Ordered to match .env.example. Defaults are the serialized values written to
# the file and must equal the Settings defaults.
FIELD_SECTIONS: list[Section] = [
    Section(
        "gmail",
        [
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE",
                "Path to your Google credentials.json (recommended; leave empty to use client id/secret)",
                "",
                "path",
            ),
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID", "OAuth client id", "", "str"
            ),
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET",
                "OAuth client secret",
                "",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_SCOPES",
                "OAuth scopes (comma-separated)",
                '["https://www.googleapis.com/auth/gmail.modify"]',
                "list",
            ),
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_TOKEN_STORAGE_PATH",
                "Where to store the encrypted token",
                "token.json",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY",
                "Token encryption key",
                "",
                "secret_gen",
            ),
        ],
    ),
    Section(
        "database",
        [
            Field(
                "AGENTIC_MAIL_MCP_DATABASE_URL",
                "Database URL (synchronous driver)",
                "sqlite:///./agentic_mail_mcp.db",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_DATABASE_DRIVER", "Database driver", "sqlite", "str"
            ),
            Field(
                "AGENTIC_MAIL_MCP_DATABASE_CACHE_TTL_SECONDS",
                "Read-through cache TTL (seconds)",
                "900",
                "int",
            ),
        ],
    ),
    Section(
        "railguards",
        [
            Field(
                "AGENTIC_MAIL_MCP_RAILGUARDS_ACCESS_LEVEL",
                "Access level",
                "read_only",
                "choice",
                ("read_only", "read_write"),
            ),
            Field(
                "AGENTIC_MAIL_MCP_RAILGUARDS_ALLOWED_RECIPIENTS",
                "Allowed forward recipients (comma-separated; empty = no restriction)",
                "[]",
                "list",
            ),
            Field(
                "AGENTIC_MAIL_MCP_RAILGUARDS_BLOCKED_ACTIONS",
                "Blocked actions (comma-separated, e.g. permanent_delete)",
                "[]",
                "list",
            ),
            Field(
                "AGENTIC_MAIL_MCP_RAILGUARDS_RATE_LIMITS",
                'Rate limits as JSON object (e.g. {"forward": 50})',
                "{}",
                "dict",
            ),
            Field(
                "AGENTIC_MAIL_MCP_RAILGUARDS_ARCHIVE_FIRST_POLICY",
                "Require archive before permanent delete?",
                "false",
                "bool",
            ),
        ],
    ),
    Section(
        "mcp",
        [
            Field(
                "AGENTIC_MAIL_MCP_MCP_SERVER_NAME",
                "MCP server name",
                "Agentic-Mail-MCP",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_MCP_TRANSPORT",
                "Transport",
                "stdio",
                "choice",
                ("stdio", "http"),
            ),
            Field(
                "AGENTIC_MAIL_MCP_MCP_HOST", "HTTP transport host", "127.0.0.1", "str"
            ),
            Field("AGENTIC_MAIL_MCP_MCP_PORT", "HTTP transport port", "8080", "int"),
        ],
    ),
    Section(
        "llm",
        [
            Field(
                "AGENTIC_MAIL_MCP_LLM_PROVIDER",
                "LLM provider",
                "openai",
                "choice",
                ("openai", "llamacpp"),
            ),
            Field("AGENTIC_MAIL_MCP_LLM_MODEL", "LLM model", "gpt-4", "str"),
            Field(
                "AGENTIC_MAIL_MCP_LLM_API_KEY",
                "LLM API key (optional; empty runs caller-first with no digests)",
                "",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_LLM_BASE_URL",
                "OpenAI-compatible base URL (optional)",
                "",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_LLM_MODEL_PATH",
                "Local llama.cpp model path (optional)",
                "",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_LLM_INTERNAL_TOOLS",
                "Expose per-email reasoning as server-side tools?",
                "false",
                "bool",
            ),
        ],
    ),
    Section(
        "search",
        [
            Field(
                "AGENTIC_MAIL_MCP_SEARCH_BACKEND",
                "Vector search backend",
                "sqlite_vss",
                "choice",
                ("sqlite_vss", "pgvector"),
            ),
            Field(
                "AGENTIC_MAIL_MCP_SEARCH_EMBEDDING_MODEL",
                "Embedding model",
                "BAAI/bge-small-en-v1.5",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_SEARCH_EMBEDDING_DIMENSION",
                "Embedding dimension",
                "384",
                "int",
            ),
        ],
    ),
    Section(
        "notifications",
        [
            Field(
                "AGENTIC_MAIL_MCP_NOTIFICATIONS_WEBHOOK_URL",
                "Outbound webhook URL (optional)",
                "",
                "str",
            ),
            Field(
                "AGENTIC_MAIL_MCP_NOTIFICATIONS_REDIS_URL",
                "Redis URL for pub/sub (optional)",
                "",
                "str",
            ),
        ],
    ),
    Section(
        "logging",
        [
            Field(
                "AGENTIC_MAIL_MCP_LOGGING_LEVEL",
                "Log level",
                "INFO",
                "choice",
                ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"),
            ),
            Field(
                "AGENTIC_MAIL_MCP_LOGGING_JSON_FORMAT",
                "JSON structured logs?",
                "true",
                "bool",
            ),
        ],
    ),
]

_TRUE = {"true", "t", "yes", "y", "1"}
_FALSE = {"false", "f", "no", "n", "0"}


def _parse(field: Field, raw: str) -> str:
    """Parse and re-serialize a raw answer; raise ValueError on invalid input."""
    if field.kind == "int":
        return str(int(raw))  # ValueError propagates
    if field.kind == "bool":
        low = raw.lower()
        if low in _TRUE:
            return "true"
        if low in _FALSE:
            return "false"
        raise ValueError("enter yes/no (or true/false)")
    if field.kind == "choice":
        if raw not in field.choices:
            raise ValueError(f"choose one of: {', '.join(field.choices)}")
        return raw
    if field.kind == "list":
        items = [part.strip() for part in raw.split(",") if part.strip()]
        return json.dumps(items)
    if field.kind == "dict":
        try:
            obj = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON object: {exc}") from exc
        if not isinstance(obj, dict):
            raise ValueError('expected a JSON object, e.g. {"forward": 50}')
        return json.dumps(obj)
    if field.kind == "path":
        path = Path(raw).expanduser()
        if not path.exists():
            raise ValueError(f"no file at {path} — check the path or leave empty")
        return str(path)
    return raw  # str


def _prompt_text(field: Field) -> str:
    if field.kind == "secret_gen":
        return f"{field.label} [auto-generate if empty]: "
    if field.kind == "choice":
        return f"{field.label} ({'/'.join(field.choices)}) [{field.default}]: "
    shown = field.default if field.default != "" else "empty"
    return f"{field.label} [{shown}]: "


def _emit(out: TextIO, message: str) -> None:
    out.write(message + "\n")


def _ask(
    field: Field,
    prompt: Callable[[str], str],
    out: TextIO,
    key_factory: Callable[[], str],
) -> str:
    """Prompt for one field, re-prompting until a valid value is given."""
    while True:
        raw = prompt(_prompt_text(field)).strip()
        if raw == "":
            if field.kind == "secret_gen":
                return key_factory()
            return field.default
        try:
            return _parse(field, raw)
        except ValueError as exc:
            _emit(out, f"  ✗ {exc}")


def _render(values: dict[str, str]) -> str:
    lines = ["# Generated by `agentic-mail-mcp init`. Safe to edit by hand."]
    for section in FIELD_SECTIONS:
        lines.append("")
        lines.append(f"# {section.name}")
        for fld in section.fields:
            lines.append(f"{fld.key}={values[fld.key]}")
    return "\n".join(lines) + "\n"


def _validate_values(values: dict[str, str]) -> None:
    """Load ``values`` through Settings to guarantee the result is loadable.

    Injects the keys into ``os.environ`` (which outranks any ``.env`` in the cwd)
    so a nearby file cannot mask the values under test, then restores.
    """
    saved: dict[str, str | None] = {}
    try:
        for key, value in values.items():
            saved[key] = os.environ.get(key)
            os.environ[key] = value
        Settings.from_env()
    finally:
        for key, old in saved.items():
            if old is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = old


def run_init(
    *,
    prompt: Callable[[str], str] = input,
    out: TextIO = sys.stdout,
    env_path: Path | str = Path(".env"),
    key_factory: Callable[[], str] | None = None,
) -> int:
    """Run the guided wizard and write ``env_path``. Returns a process exit code."""
    env_path = Path(env_path)
    generate_key = key_factory or (lambda: secrets.token_urlsafe(32))

    _emit(out, "Configure agentic-mail-mcp — press Enter to accept each [default].")

    try:
        if env_path.exists():
            answer = (
                prompt(f"{env_path} already exists. Overwrite? [y/N]: ").strip().lower()
            )
            if answer not in {"y", "yes"}:
                _emit(out, f"Aborted — {env_path} left unchanged.")
                return 1

        values: dict[str, str] = {}
        for section in FIELD_SECTIONS:
            _emit(out, f"\n[{section.name}]")
            for fld in section.fields:
                values[fld.key] = _ask(fld, prompt, out, generate_key)

        _validate_values(values)
    except EOFError:
        _emit(out, "\nAborted — no file written.")
        return 1

    if env_path.exists():
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
        backup = env_path.with_name(f"{env_path.name}.bak-{stamp}")
        shutil.copy2(env_path, backup)
        _emit(out, f"Backed up previous config to {backup}")

    env_path.write_text(_render(values))
    try:
        os.chmod(env_path, 0o600)
    except OSError:  # pragma: no cover - platform dependent
        pass

    _emit(out, f"\n✅ Wrote {env_path}.")
    _emit(out, "Next: run 'agentic-mail-mcp auth', then 'agentic-mail-mcp serve'.")
    return 0
