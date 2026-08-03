from __future__ import annotations

import json

from src.Common.Domain.Exceptions import NotFoundError, ValidationError
from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Gmail.Domain.Repository.email_repository import EmailRepository
from src.Intelligence.Application.DTO.dtos import ActionItemDTO
from src.Intelligence.Domain.Gateway.llm_gateway import LlmGateway
from src.Intelligence.Domain.ValueObjects.prompt_template import PromptTemplate

_SYSTEM_PROMPT = (
    "You extract action items from emails. Respond ONLY with a JSON array of "
    'objects each containing "description" (string), optional "due_date" '
    '(ISO date string or null), and optional "priority" (1-5).'
)
_TEMPLATE = PromptTemplate(
    name="extract_action_items",
    template="Extract action items from this email.\nSubject: {subject}\n\n{body}",
)


class ExtractActionItemsUseCase:
    def __init__(
        self,
        email_repository: EmailRepository,
        llm: LlmGateway,
        *,
        model: str = "default",
        max_tokens: int = 256,
    ) -> None:
        self._email_repository = email_repository
        self._llm = llm
        self._model = model
        self._max_tokens = max_tokens

    def execute(self, email_id: UUIDId) -> list[ActionItemDTO]:
        email = self._email_repository.find_by_id(email_id)
        if email is None:
            raise NotFoundError(f"Email not found: {email_id}")

        prompt = _TEMPLATE.render(subject=email.subject, body=email.body)
        response = self._llm.generate(
            prompt, _SYSTEM_PROMPT, self._max_tokens, self._model
        )

        try:
            parsed = json.loads(response.text)
            if not isinstance(parsed, list):
                raise TypeError("expected a JSON array")
        except (json.JSONDecodeError, TypeError) as exc:
            raise ValidationError(
                f"LLM action-item response could not be parsed: {response.text!r}"
            ) from exc

        items: list[ActionItemDTO] = []
        for entry in parsed:
            items.append(
                ActionItemDTO(
                    description=str(entry["description"]),
                    due_date=entry.get("due_date"),
                    priority=int(entry.get("priority", 3)),
                )
            )
        return items
