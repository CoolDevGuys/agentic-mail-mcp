from __future__ import annotations

import base64
import hashlib
import logging
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from src.Common.Domain.Exceptions import DomainError

logger = logging.getLogger(__name__)


def _derive_fernet_key(secret: str) -> bytes:
    """Derive a valid Fernet key from an arbitrary secret string."""
    if not secret:
        raise DomainError("token_encryption_key must be set to store OAuth tokens")
    digest = hashlib.sha256(secret.encode("utf-8")).digest()
    return base64.urlsafe_b64encode(digest)


class GmailOAuthProvider:
    """Persists OAuth refresh tokens encrypted at rest.

    Token values are never logged. The interactive and headless Google flows
    build ``google.oauth2.credentials.Credentials`` from the decrypted token
    JSON; this class owns the encrypted persistence.
    """

    def __init__(
        self,
        token_storage_path: str,
        encryption_key: str,
        *,
        scopes: list[str] | None = None,
        client_config: dict | None = None,
    ) -> None:
        self._path = Path(token_storage_path).expanduser()
        self._fernet = Fernet(_derive_fernet_key(encryption_key))
        self._scopes = scopes or ["https://www.googleapis.com/auth/gmail.modify"]
        self._client_config = client_config

    def save_token(self, token_json: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        encrypted = self._fernet.encrypt(token_json.encode("utf-8"))
        self._path.write_bytes(encrypted)
        logger.info("Stored encrypted OAuth token", extra={"path": str(self._path)})

    def load_token(self) -> str:
        if not self._path.exists():
            raise DomainError(f"No stored token at {self._path}")
        encrypted = self._path.read_bytes()
        try:
            return self._fernet.decrypt(encrypted).decode("utf-8")
        except InvalidToken as exc:
            raise DomainError(
                "Stored OAuth token could not be decrypted with the configured key"
            ) from exc

    def has_token(self) -> bool:
        return self._path.exists()

    def authorize_interactive(self) -> str:  # pragma: no cover - opens a browser
        from google_auth_oauthlib.flow import InstalledAppFlow

        if self._client_config is None:
            raise DomainError("client_config is required for interactive authorization")
        flow = InstalledAppFlow.from_client_config(self._client_config, self._scopes)
        credentials = flow.run_local_server(port=0)
        token_json = credentials.to_json()
        self.save_token(token_json)
        return token_json

    def load_credentials(self):  # pragma: no cover - requires google credentials
        from google.oauth2.credentials import Credentials

        return Credentials.from_authorized_user_info(
            __import__("json").loads(self.load_token()), self._scopes
        )
