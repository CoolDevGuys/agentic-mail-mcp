from __future__ import annotations

from dataclasses import replace

from agentic_mail_mcp.Gmail.Application.DTO.dtos import EmailDTO, SearchEmailsResult
from agentic_mail_mcp.Gmail.Application.Queries.queries import SearchEmailsQuery
from agentic_mail_mcp.Gmail.Domain.Gateway.gmail_gateway import GmailGateway
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailQuery

# Page size for the id-walk that computes the exact total. Gmail caps
# messages.list at 500, so this stays within the limit while minimizing
# round-trips.
_ID_PAGE_SIZE = 500

# Gmail has no is:received operator; "received" is everything that is not
# sent, a draft, spam, trash, or a chat.
_RECEIVED_EXCLUSIONS = "-in:sent -in:draft -in:spam -in:trash -in:chats"


def _scoped_query_term(query: SearchEmailsQuery) -> str:
    """Apply the free-text term according to ``query_scope``.

    ``subject``/``body`` restrict the term to the Gmail ``subject:``/``inbody:``
    operators (Gmail needs quotes for multi-word values); a term already
    containing double quotes is passed through unquoted rather than corrupted.
    """
    term = query.query_string
    if query.query_scope == "all":
        return term
    operator = "subject" if query.query_scope == "subject" else "inbody"
    if '"' in term:
        return f"{operator}:{term}"
    return f'{operator}:"{term}"'


def build_gmail_query(query: SearchEmailsQuery) -> GmailQuery:
    """Compose a GmailQuery string from the structured search criteria."""
    parts: list[str] = []
    if query.query_string:
        parts.append(_scoped_query_term(query))
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
    if query.direction == "sent":
        parts.append("in:sent")
    elif query.direction == "received":
        parts.append(_RECEIVED_EXCLUSIONS)
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
        all_ids = self._collect_message_ids(gmail_query.value)
        ids = [mid for mid in all_ids if mid not in query.seen_ids]
        total_count = len(ids)
        start = (query.page - 1) * query.page_size
        page_ids = ids[start : start + query.page_size]
        headers = self._gateway.batch_get_metadata(
            page_ids, include_body=query.include_body
        )
        emails = [EmailDTO.from_gateway_header(h) for h in headers]
        if query.body_max_length is not None:
            emails = [self._truncate(e, query.body_max_length) for e in emails]
        return SearchEmailsResult(
            emails=emails,
            page=query.page,
            page_size=query.page_size,
            total_count=total_count,
        )

    def _collect_message_ids(self, q: str) -> list[str]:
        """Walk every ``messages.list`` page and return all matching ids, in
        Gmail's default order (newest first)."""
        ids: list[str] = []
        page_token: str | None = None
        while True:
            page = self._gateway.list_message_ids(q, page_token, _ID_PAGE_SIZE)
            ids.extend(page.message_ids)
            if not page.next_page_token:
                return ids
            page_token = page.next_page_token

    @staticmethod
    def _truncate(email: EmailDTO, max_length: int) -> EmailDTO:
        if len(email.body) <= max_length:
            return email
        return replace(email, body=email.body[:max_length])

    def _search_cache(
        self, query: SearchEmailsQuery, gmail_query: GmailQuery
    ) -> SearchEmailsResult:
        matches = self._repository.search(gmail_query.value)
        if query.seen_ids:
            matches = [
                e for e in matches if e.message_id.value not in query.seen_ids
            ]
        total_count = len(matches)
        start = (query.page - 1) * query.page_size
        end = start + query.page_size
        page_items = matches[start:end]
        emails = [EmailDTO.from_entity(e) for e in page_items]
        if query.body_max_length is not None:
            emails = [self._truncate(e, query.body_max_length) for e in emails]
        return SearchEmailsResult(
            emails=emails,
            page=query.page,
            page_size=query.page_size,
            total_count=total_count,
        )
