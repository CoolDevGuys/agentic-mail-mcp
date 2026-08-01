from dataclasses import dataclass

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.base import ValueObject


@dataclass(frozen=True)
class ModelConfig(ValueObject):
    provider: str
    model_id: str
    max_tokens: int
    temperature: float

    def __post_init__(self) -> None:
        if self.max_tokens <= 0:
            raise ValidationError(f"max_tokens must be > 0, got {self.max_tokens}")
        if not 0.0 <= self.temperature <= 1.0:
            raise ValidationError(
                f"temperature must be between 0.0 and 1.0, got {self.temperature}"
            )
