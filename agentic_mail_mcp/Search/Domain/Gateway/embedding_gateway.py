from __future__ import annotations

from typing import Protocol


class EmbeddingGateway(Protocol):
    def embed(self, text: str) -> list[float]: ...

    def dimension(self) -> int: ...
