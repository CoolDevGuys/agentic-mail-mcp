from __future__ import annotations

from src.Common.Domain.Events import EventBus
from src.Common.Infrastructure.Clock import Clock, SystemClock
from src.Gmail.Domain.Events import EmailReceived, InboxSynchronized
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from src.Gmail.Domain.Mapper.email_mapper import EmailMapper
from src.Gmail.Domain.Repository.email_repository import EmailRepository


class GmailHistorySynchronizer:
    """Applies Gmail history deltas to the local cache and emits domain events.

    Idempotent: messages already present in the repository are skipped, so
    re-running for the same start history id applies no duplicate changes.
    """

    def __init__(
        self,
        gateway: GmailGateway,
        email_repository: EmailRepository,
        event_bus: EventBus,
        *,
        clock: Clock | None = None,
    ) -> None:
        self._gateway = gateway
        self._email_repository = email_repository
        self._event_bus = event_bus
        self._clock = clock or SystemClock()

    def synchronize(self, start_history_id: str) -> int:
        history = self._gateway.get_history(start_history_id, start_history_id)
        new_count = 0

        for header in history.messages:
            if self._email_repository.find_by_gmail_message_id(header.id) is not None:
                continue
            full = self._gateway.get_message(header.id, "full")
            if full is None:
                continue
            email = EmailMapper.to_domain(full)
            self._email_repository.save(email)
            self._event_bus.publish(
                EmailReceived(
                    email_id=email.id,
                    from_address=email.from_address.value if email.from_address else "",
                    subject=email.subject,
                    received_at=email.date_sent or self._clock.now(),
                )
            )
            new_count += 1

        self._event_bus.publish(
            InboxSynchronized(history_id=history.history_id, email_count=new_count)
        )
        return new_count
