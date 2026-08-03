from __future__ import annotations

from src.Gmail.Application.DTO.dtos import EmailDTO, SearchEmailsResult
from src.Gmail.Application.Queries.queries import SearchEmailsQuery
from src.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Gmail.Domain.ValueObjects import GmailQuery


def build_gmail_query(query: SearchEmailsQuery) -> GmailQuery:
    """Compose a GmailQuery string from the structured search criteria."""
    parts: list[str] = []
    if query.query_string:
        parts.append(query.query_string)
    if query.from_address:
        parts.append(f"from:{query.from_address}")
    if query.to_address:
        parts.append(f"to:{query.to_address}")
    if query.subject:
        parts.append(f"subject:{query.subject}")
    if query.date_from:
        parts.append(f"after:{query.date_from.isoformat()}")
    if query.date_to:
        parts.append(f"before:{query.date_to.isoformat()}")
    if query.has_attachment:
        parts.append("has:attachment")
    if query.label:
        parts.append(f"label:{query.label}")
    if query.unread_only:
        parts.append("is:unread")
    if not parts:
        parts.append("in:inbox")
    return GmailQuery(value=" ".join(parts))


class SearchEmailsUseCase:
    """Search emails via the live Gmail API or the local cache.

    When ``use_cache`` is True results are resolved from the EmailRepository;
    otherwise the GmailGateway is queried live (the default).
    """

    def __init__(
        self,
        gateway: GmailGateway,
        repository: EmailRepository,
        *,
        use_cache: bool = False,
    ) -> None:
        self._gateway = gateway
        self._repository = repository
        self._use_cache = use_cache

    def execute(self, query: SearchEmailsQuery) -> SearchEmailsResult:
        gmail_query = build_gmail_query(query)
        if self._use_cache:
            return self._search_cache(query, gmail_query)
        return self._search_live(query, gmail_query)

    def _search_live(
        self, query: SearchEmailsQuery, gmail_query: GmailQuery
    ) -> SearchEmailsResult:
        response = self._gateway.list_messages(
            gmail_query.value, query.page_token, query.page_size
        )
        emails = [EmailDTO.from_gateway_header(h) for h in response.messages]
        return SearchEmailsResult(
            emails=emails,
            page=query.page,
            page_size=query.page_size,
            next_page_token=response.next_page_token,
            total_estimate=response.result_size_estimate,
        )

    def _search_cache(
        self, query: SearchEmailsQuery, gmail_query: GmailQuery
    ) -> SearchEmailsResult:
        matches = self._repository.search(gmail_query.value)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_items = matches[start:end]
        emails = [EmailDTO.from_entity(e) for e in page_items]
        return SearchEmailsResult(
            emails=emails,
            page=query.page,
            page_size=query.page_size,
            next_page_token=None,
            total_estimate=len(matches),
        )
