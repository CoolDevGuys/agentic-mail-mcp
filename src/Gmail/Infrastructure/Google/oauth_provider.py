from __future__ import annotations

import base64
import logging
import os
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from src.Common.Domain.Exceptions import DomainError

logger = logging.getLogger(__name__)

_SALT_BYTES = 16
# scrypt cost parameters (memory-hard); tolerant of low-entropy passphrases.
_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1


def _derive_fernet_key(secret: str, salt: bytes) -> bytes:
    """Derive a Fernet key from a secret using salted scrypt."""
    if not secret:
        raise DomainError("token_encryption_key must be set to store OAuth tokens")
    kdf = Scrypt(salt=salt, length=32, n=_SCRYPT_N, r=_SCRYPT_R, p=_SCRYPT_P)
    return base64.urlsafe_b64encode(kdf.derive(secret.encode("utf-8")))


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
        if not encryption_key:
            raise DomainError("token_encryption_key must be set to store OAuth tokens")
        self._path = Path(token_storage_path).expanduser()
        self._secret = encryption_key
        self._scopes = scopes or ["https://www.googleapis.com/auth/gmail.modify"]
        self._client_config = client_config

    def save_token(self, token_json: str) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        salt = os.urandom(_SALT_BYTES)
        fernet = Fernet(_derive_fernet_key(self._secret, salt))
        encrypted = fernet.encrypt(token_json.encode("utf-8"))
        # File layout: random salt prefix + Fernet token.
        self._path.write_bytes(salt + encrypted)
        logger.info("Stored encrypted OAuth token", extra={"path": str(self._path)})

    def load_token(self) -> str:
        if not self._path.exists():
            raise DomainError(f"No stored token at {self._path}")
        blob = self._path.read_bytes()
        salt, encrypted = blob[:_SALT_BYTES], blob[_SALT_BYTES:]
        fernet = Fernet(_derive_fernet_key(self._secret, salt))
        try:
            return fernet.decrypt(encrypted).decode("utf-8")
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
