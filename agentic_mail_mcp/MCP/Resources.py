"""MCP resources exposing read-only server state.

Resources are small JSON projections an agent can read to orient itself:
the connected account and its access level, the Gmail push-notification (watch)
status, and the vector-search index statistics. Each ``ResourceDefinition``
carries a URI and a provider callable; ``read()`` returns a JSON-compatible
payload.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agentic_mail_mcp.MCP.serialization import to_jsonable

ACCOUNT_URI = "gmail://account"
WATCH_URI = "gmail://watch"
INDEX_URI = "search://index"


def _default_watch_status() -> dict[str, Any]:
    return {"active": False, "history_id": None}


@dataclass
class ResourceContext:
    """Data sources backing the MCP resources.

    ``watch_status_provider`` and ``index_count_provider`` are callables so the
    resource reflects live state each time it is read.
    """

    account_email: str
    access_level: str
    watch_status_provider: Callable[[], dict[str, Any]] = _default_watch_status
    index_count_provider: Callable[[], int] = lambda: 0


@dataclass(frozen=True)
class ResourceDefinition:
    uri: str
    name: str
    description: str
    provider: Callable[[], Any]
    mime_type: str = "application/json"

    def read(self) -> Any:
        return to_jsonable(self.provider())


def build_resources(context: ResourceContext) -> list[ResourceDefinition]:
    return [
        ResourceDefinition(
            uri=ACCOUNT_URI,
            name="account-info",
            description="Connected Gmail account and its railguard access level.",
            provider=lambda: {
                "email": context.account_email,
                "access_level": context.access_level,
            },
        ),
        ResourceDefinition(
            uri=WATCH_URI,
            name="watch-status",
            description="Gmail push-notification (watch) subscription status.",
            provider=context.watch_status_provider,
        ),
        ResourceDefinition(
            uri=INDEX_URI,
            name="index-status",
            description="Vector-search index statistics.",
            provider=lambda: {"document_count": context.index_count_provider()},
        ),
    ]
