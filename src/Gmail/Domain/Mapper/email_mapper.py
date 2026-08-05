from __future__ import annotations

from datetime import datetime

from src.Gmail.Domain.Entities.email import Email
from src.Gmail.Domain.Gateway.gmail_gateway import GmailMessage


class EmailMapper:
    @staticmethod
    def to_domain(gateway_message: GmailMessage) -> Email:
        to_addresses = gateway_message.to.split(",") if gateway_message.to else []

        date_sent = None
        if gateway_message.date:
            try:
                date_sent = datetime.fromisoformat(
                    gateway_message.date.removesuffix("Z")
                )
            except (ValueError, AttributeError):
                date_sent = None

        return Email.from_gmail_message(
            message_id=gateway_message.id,
            thread_id=gateway_message.thread_id,
            snippet=gateway_message.snippet,
            subject=gateway_message.subject,
            from_address=gateway_message.from_ or None,
            to_addresses=to_addresses,
            date_sent=date_sent,
            body=gateway_message.body,
            labels=gateway_message.labels,
        )
