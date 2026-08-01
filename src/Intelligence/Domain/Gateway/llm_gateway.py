from dataclasses import dataclass
from typing import Protocol


@dataclass
class Usage:
    input_tokens: int
    output_tokens: int


@dataclass
class LlmResponse:
    text: str
    model: str
    usage: Usage


class LlmGateway(Protocol):
    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        model: str,
    ) -> LlmResponse: ...
