from dataclasses import dataclass, field
from datetime import UTC, datetime


@dataclass
class JobsScraped:
    """Published once per completed page of scraped jobs."""

    event_type: str
    run_id: str
    count: int
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
