from dataclasses import dataclass, field
from datetime import UTC, datetime

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError

VALID_DIGEST_TYPES = {"daily", "weekly"}


@dataclass
class DigestReady:
    digest_type: str
    digest_period: str
    email_count: int
    generated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if self.digest_type not in VALID_DIGEST_TYPES:
            raise ValidationError(f"digest_type must be one of {VALID_DIGEST_TYPES}")
