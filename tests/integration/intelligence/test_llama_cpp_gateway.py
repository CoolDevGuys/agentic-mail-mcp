from __future__ import annotations

import httpx
import pytest
import respx

from agentic_mail_mcp.Common.Domain.Exceptions import DomainError
from agentic_mail_mcp.Intelligence.Domain.Gateway.llm_gateway import LlmResponse
from agentic_mail_mcp.Intelligence.Infrastructure.LlamaCpp.llama_cpp_gateway import (
    LlamaCppGateway,
)

_URL = "https://llm.example.com/v1/chat/completions"


def _gateway() -> LlamaCppGateway:
    return LlamaCppGateway(
        provider="openai", api_key="k", base_url="https://llm.example.com/v1"
    )


class TestRemoteGeneration:
    @respx.mock
    def test_generate_maps_response(self) -> None:
        respx.post(_URL).mock(
            return_value=httpx.Response(
                200,
                json={
                    "model": "gpt-4",
                    "choices": [{"message": {"content": "a summary"}}],
                    "usage": {"prompt_tokens": 12, "completion_tokens": 5},
                },
            )
        )
        result = _gateway().generate("prompt", "system", 256, "gpt-4")
        assert isinstance(result, LlmResponse)
        assert result.text == "a summary"
        assert result.model == "gpt-4"
        assert result.usage.input_tokens == 12
        assert result.usage.output_tokens == 5

    @respx.mock
    def test_request_carries_prompt_and_auth(self) -> None:
        route = respx.post(_URL).mock(
            return_value=httpx.Response(
                200, json={"choices": [{"message": {"content": "x"}}]}
            )
        )
        _gateway().generate("hello prompt", "sys", 128, "gpt-4")
        request = route.calls.last.request
        assert request.headers["Authorization"] == "Bearer k"
        body = request.content.decode()
        assert "hello prompt" in body and "sys" in body

    @respx.mock
    def test_error_status_raises_domain_error(self) -> None:
        respx.post(_URL).mock(return_value=httpx.Response(500, text="boom"))
        with pytest.raises(DomainError):
            _gateway().generate("p", "s", 64, "gpt-4")

    @respx.mock
    def test_transport_error_raises_domain_error(self) -> None:
        respx.post(_URL).mock(side_effect=httpx.ConnectError("down"))
        with pytest.raises(DomainError):
            _gateway().generate("p", "s", 64, "gpt-4")

    @respx.mock
    def test_malformed_response_raises_domain_error(self) -> None:
        respx.post(_URL).mock(return_value=httpx.Response(200, json={"nope": 1}))
        with pytest.raises(DomainError):
            _gateway().generate("p", "s", 64, "gpt-4")


class TestLocalGeneration:
    def test_missing_llama_cpp_raises_domain_error(self) -> None:
        pytest.importorskip  # noqa: B018 - readability
        try:
            import llama_cpp  # noqa: F401
        except ImportError:
            gateway = LlamaCppGateway(provider="llamacpp", model_path="/nonexistent")
            with pytest.raises(DomainError):
                gateway.generate("p", "s", 64, "local-model")
        else:  # pragma: no cover - only when the optional dep is installed
            pytest.skip("llama-cpp-python is installed; skipping the missing-dep path")
