from __future__ import annotations

import json

from src.Common.Domain.Exceptions import NotFoundError, ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.Clock import Clock
from src.Common.Infrastructure.IdGenerator import IdGenerator
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Intelligence.Application.DTO.dtos import ClassificationDTO
from src.Intelligence.Domain.Entities.classification import Classification
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Intelligence.Domain.Repository.repositories import ClassificationRepository
from src.Intelligence.Domain.ValueObjects.prompt_template import PromptTemplate

_SYSTEM_PROMPT = (
    "You are an email classifier. Respond ONLY with a JSON object containing "
    '"category" (one of urgent, normal, spam, promo), "priority" (1-5), and '
    '"confidence" (0.0-1.0).'
)
_TEMPLATE = PromptTemplate(
    name="classify_email",
    template="Classify this email.\nSubject: {subject}\n\n{body}",
)


class ClassifyEmailUseCase:
    def __init__(
        self,
        email_repository: EmailRepository,
        llm: LlmGateway,
        classification_repository: ClassificationRepository,
        clock: Clock,
        id_generator: IdGenerator,
        *,
        model: str = "default",
        max_tokens: int = 128,
    ) -> None:
        self._email_repository = email_repository
        self._llm = llm
        self._classification_repository = classification_repository
        self._clock = clock
        self._id_generator = id_generator
        self._model = model
        self._max_tokens = max_tokens

    def execute(self, email_id: UUIDId) -> ClassificationDTO:
        email = self._email_repository.find_by_id(email_id)
        if email is None:
            raise NotFoundError(f"Email not found: {email_id}")

        prompt = _TEMPLATE.render(subject=email.subject, body=email.body)
        response = self._llm.generate(
            prompt, _SYSTEM_PROMPT, self._max_tokens, self._model
        )

        try:
            parsed = json.loads(response.text)
            category = str(parsed["category"])
            priority = int(parsed["priority"])
            confidence = float(parsed["confidence"])
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
            raise ValidationError(
                f"LLM classification response could not be parsed: {response.text!r}"
            ) from exc

        classification = Classification(
            id=self._id_generator.generate(),
            email_id=email.id,
            category=category,
            priority=priority,
            confidence=confidence,
            model_used=response.model,
            created_at=self._clock.now(),
        )
        self._classification_repository.save(classification)
        return ClassificationDTO.from_entity(classification)
