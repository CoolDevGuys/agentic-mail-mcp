from __future__ import annotations

from src.Common.Domain.Exceptions import NotFoundError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.Clock import Clock
from src.Common.Infrastructure.IdGenerator import IdGenerator
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Intelligence.Application.DTO.dtos import SuggestionDTO
from src.Intelligence.Domain.Entities.suggestion import Suggestion
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Intelligence.Domain.Repository.repositories import SuggestionRepository
from src.Intelligence.Domain.ValueObjects.prompt_template import PromptTemplate

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

    def execute(self, email_id: UUIDId) -> SuggestionDTO:
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
