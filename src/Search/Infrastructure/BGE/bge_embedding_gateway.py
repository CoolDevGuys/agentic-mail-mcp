from __future__ import annotations

from collections.abc import Callable, Sequence

from src.Common.Domain.Exceptions import ValidationError

Encoder = Callable[[str], Sequence[float]]


class BgeEmbeddingGateway:
    """EmbeddingGateway backed by a BGE sentence-transformer model.

    The encoder is injectable so tests (and lightweight deployments) can supply
    a deterministic function without loading the model weights. When no encoder
    is provided the BGE model is lazily loaded on first use.
    """

    def __init__(
        self,
        *,
        model_name: str = "BAAI/bge-small-en-v1.5",
        dimension: int = 384,
        encoder: Encoder | None = None,
    ) -> None:
        self._model_name = model_name
        self._dimension = dimension
        self._encoder = encoder

    def _get_encoder(self) -> Encoder:
        if self._encoder is None:  # pragma: no cover - requires model download
            from sentence_transformers import SentenceTransformer

            model = SentenceTransformer(self._model_name)
            self._encoder = lambda text: model.encode(text).tolist()
        return self._encoder

    def embed(self, text: str) -> list[float]:
        vector = [float(v) for v in self._get_encoder()(text)]
        if len(vector) != self._dimension:
            raise ValidationError(
                f"Embedding dimension {len(vector)} does not match configured "
                f"dimension {self._dimension}"
            )
        return vector

    def dimension(self) -> int:
        return self._dimension
