"""Preflight verification of Google credentials and the stored OAuth token.

``check_auth`` sequences the prerequisites — client config, encryption key,
stored token — and then makes a **live** Gmail call (``get_profile``) to prove
the refresh token is still valid. It returns a structured result so both the
``verify-auth`` command (which sets an exit code) and the HTTP-startup hook
(which logs a warning) can share one implementation.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from agentic_mail_mcp.Bootstrap.Composition import (
    build_oauth_provider,
    resolve_client_config,
)
from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.Common.Domain.Exceptions import DomainError


@dataclass(frozen=True)
class AuthCheckResult:
    """Outcome of an auth preflight.

    ``stage`` is ``"ok"`` on success, otherwise the first failing prerequisite:
    ``no_client``, ``no_key``, ``no_token``, ``token_rejected`` (Google rejected
    the token — expired/revoked/undecryptable), or ``unreachable`` (network or
    other transient error).
    """

    ok: bool
    stage: str
    message: str
    account: str | None = None


def _default_gateway_factory(credentials: Any) -> Any:
    from agentic_mail_mcp.Gmail.Infrastructure.Google.gmail_api_gateway import (
        GmailApiGateway,
    )

    return GmailApiGateway.from_credentials(credentials)


def _looks_like_auth_error(exc: Exception) -> bool:
    """True when the failure means the token itself is bad, not connectivity."""
    if isinstance(exc, DomainError):
        # e.g. the stored token could not be decrypted with the configured key.
        return True
    name = type(exc).__name__
    if name in {"RefreshError", "DefaultCredentialsError"}:
        return True
    status = getattr(exc, "status_code", None) or getattr(
        getattr(exc, "resp", None), "status", None
    )
    if status == 401:
        return True
    text = str(exc).lower()
    return any(
        token in text
        for token in ("invalid_grant", "invalid_token", "unauthorized", "revoked")
    )


def check_auth(
    settings: Settings,
    *,
    gateway_factory: Callable[[Any], Any] = _default_gateway_factory,
) -> AuthCheckResult:
    """Verify the server can authenticate to Gmail with the current config."""
    if resolve_client_config(settings) is None:
        return AuthCheckResult(
            ok=False,
            stage="no_client",
            message=(
                "No Google client configured. Set "
                "AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE (the credentials.json "
                "you downloaded), or AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID and "
                "AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET."
            ),
        )

    if not settings.gmail.token_encryption_key:
        return AuthCheckResult(
            ok=False,
            stage="no_key",
            message=(
                "Missing AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY — it is needed "
                "to read the stored token."
            ),
        )

    provider = build_oauth_provider(settings)
    if not provider.has_token():
        return AuthCheckResult(
            ok=False,
            stage="no_token",
            message=(
                "No stored token. Run `agentic-mail-mcp auth` once to authorize and "
                "store the encrypted token."
            ),
        )

    try:
        gateway = gateway_factory(provider.load_credentials())
        account = gateway.get_profile()
    except Exception as exc:  # noqa: BLE001 - classified below into an actionable result
        if _looks_like_auth_error(exc):
            return AuthCheckResult(
                ok=False,
                stage="token_rejected",
                message=(
                    f"The stored token is no longer valid ({exc}). It may be expired "
                    "or revoked — re-run `agentic-mail-mcp auth`."
                ),
            )
        return AuthCheckResult(
            ok=False,
            stage="unreachable",
            message=(
                f"Could not reach Gmail to verify the token ({exc}). Check "
                "connectivity and try again."
            ),
        )

    return AuthCheckResult(
        ok=True,
        stage="ok",
        message=f"Authorized as {account}.",
        account=account,
    )
