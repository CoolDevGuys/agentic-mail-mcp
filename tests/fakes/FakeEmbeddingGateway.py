import math
from typing import Any


class FakeEmbeddingGateway:
    def __init__(self, dimension: int = 768) -> None:
        self._dimension = dimension
        self._embeddings: dict[str, list[float]] = {}
        self._calls: list[dict] = []

    async def embed(self, text: str) -> list[float]:
        self._calls.append({"text": text})
        vector = [hash(f"{text}_{i}") % 1000 / 1000.0 for i in range(self._dimension)]
        norm = math.sqrt(sum(v * v for v in vector)) or 1.0
        vector = [v / norm for v in vector]
        self._embeddings[text] = vector
        return vector

    async def similarity_search(
        self, query: str, limit: int = 5, threshold: float = 0.8
    ) -> list[dict[str, Any]]:
        query_vec = await self.embed(query)
        results = []
        for text, vec in self._embeddings.items():
            similarity = sum(a * b for a, b in zip(query_vec, vec))
            if similarity >= threshold:
                results.append({"text": text, "score": similarity})
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:limit]

    def get_calls(self) -> list[dict]:
        return self._calls
