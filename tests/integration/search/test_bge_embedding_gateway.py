from __future__ import annotations

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Search.Infrastructure.BGE.bge_embedding_gateway import (
    BgeEmbeddingGateway,
)


def _fake_encoder(dimension: int):
    def encode(text: str) -> list[float]:
        return [float((hash((text, i)) % 1000) / 1000.0) for i in range(dimension)]

    return encode


class TestBgeEmbeddingGateway:
    def test_embed_length_matches_dimension(self) -> None:
        gateway = BgeEmbeddingGateway(dimension=8, encoder=_fake_encoder(8))
        vector = gateway.embed("hello")
        assert len(vector) == 8
        assert gateway.dimension() == 8
        assert all(isinstance(v, float) for v in vector)

    def test_embedding_is_deterministic(self) -> None:
        gateway = BgeEmbeddingGateway(dimension=8, encoder=_fake_encoder(8))
        assert gateway.embed("same text") == gateway.embed("same text")

    def test_dimension_mismatch_raises(self) -> None:
        # Encoder returns 4 values but the gateway expects 8.
        gateway = BgeEmbeddingGateway(dimension=8, encoder=_fake_encoder(4))
        with pytest.raises(ValidationError):
            gateway.embed("text")
