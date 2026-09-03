from __future__ import annotations

from agentic_mail_mcp.Common.Domain.Exceptions import NotFoundError
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId
from agentic_mail_mcp.Common.Infrastructure.Clock import Clock
from agentic_mail_mcp.Common.Infrastructure.IdGenerator import IdGenerator
from agentic_mail_mcp.Gmail.Domain.Repository.email_repository import EmailRepository
from agentic_mail_mcp.Gmail.Domain.ValueObjects import GmailMessageId
from agentic_mail_mcp.Intelligence.Application.DTO.dtos import SuggestionDTO
from agentic_mail_mcp.Intelligence.Domain.Entities.suggestion import Suggestion
from agentic_mail_mcp.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from agentic_mail_mcp.Intelligence.Domain.Repository.repositories import (
    SuggestionRepository,
)
from agentic_mail_mcp.Intelligence.Domain.ValueObjects.prompt_template import (
    PromptTemplate,
)

_SYSTEM_PROMPT = "You are an assistant that drafts helpful email replies."
_TEMPLATE = PromptTemplate(
    name="suggest_reply",
    template="Draft a reply to this email.\nSubject: {subject}\n\n{body}",
)


class SuggestReplyUseCase:
    def __init__(
        self,
        email_repository: EmailRepository,
        llm: LlmGateway,
        suggestion_repository: SuggestionRepository,
        clock: Clock,
        id_generator: IdGenerator,
        *,
        model: str = "default",
        max_tokens: int = 512,
    ) -> None:
        self._email_repository = email_repository
        self._llm = llm
        self._suggestion_repository = suggestion_repository
        self._clock = clock
        self._id_generator = id_generator
        self._model = model
        self._max_tokens = max_tokens

    def execute(self, email_id: UUIDId | GmailMessageId) -> SuggestionDTO:
        if isinstance(email_id, GmailMessageId):
            email = self._email_repository.find_by_gmail_message_id(email_id.value)
        else:
            email = self._email_repository.find_by_id(email_id)
        if email is None:
            raise NotFoundError(f"Email not found: {email_id}")

        prompt = _TEMPLATE.render(subject=email.subject, body=email.body)
        response = self._llm.generate(
            prompt, _SYSTEM_PROMPT, self._max_tokens, self._model
        )

        suggestion = Suggestion(
            id=self._id_generator.generate(),
            email_id=email.id,
            suggestion_type="reply",
            draft_text=response.text,
            model_used=response.model,
            created_at=self._clock.now(),
        )
        self._suggestion_repository.save(suggestion)
        return SuggestionDTO.from_entity(suggestion)
