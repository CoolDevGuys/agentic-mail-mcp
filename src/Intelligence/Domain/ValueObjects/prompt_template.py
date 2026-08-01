import re
from dataclasses import dataclass
from typing import Any

from src.Common.Domain.Exceptions import ValidationError
from src.Common.Domain.ValueObjects.base import ValueObject


@dataclass(frozen=True)
class PromptTemplate(ValueObject):
    name: str
    template: str

    def render(self, **kwargs: Any) -> str:
        required = set(re.findall(r"\{(\w+)\}", self.template))
        provided = set(kwargs.keys())
        missing = required - provided
        if missing:
            raise ValidationError(
                f"Missing required variables for template {self.name!r}: {sorted(missing)}"
            )
        try:
            return self.template.format(**kwargs)
        except KeyError as e:
            raise ValidationError(
                f"Missing variable {e.args[0]!r} in template {self.name!r}"
            ) from e
