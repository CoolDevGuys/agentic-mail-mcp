from __future__ import annotations

from typing import Any

import httpx

from agentic_mail_mcp.Common.Domain.Exceptions import DomainError
from agentic_mail_mcp.Intelligence.Domain.Gateway.llm_gateway import LlmResponse, Usage

_DEFAULT_OPENAI_BASE_URL = "https://api.openai.com/v1"


class LlamaCppGateway:
    """LlmGateway backed by a local llama.cpp model or an OpenAI-compatible API.

    ``provider="llamacpp"`` runs local inference from ``model_path``; any other
    provider targets an OpenAI-compatible ``/chat/completions`` endpoint.
    """

    def __init__(
        self,
        *,
        provider: str = "openai",
        api_key: str = "",
        base_url: str = "",
        model_path: str = "",
        client: httpx.Client | None = None,
        timeout: float = 30.0,
    ) -> None:
        self._provider = provider
        self._api_key = api_key
        self._base_url = (base_url or _DEFAULT_OPENAI_BASE_URL).rstrip("/")
        self._model_path = model_path
        self._client = client or httpx.Client(timeout=timeout)
        self._local_model: Any | None = None

    @classmethod
    def from_settings(cls, settings: Any) -> LlamaCppGateway:
        llm = settings.llm
        return cls(
            provider=llm.provider,
            api_key=llm.api_key,
            base_url=llm.base_url,
            model_path=llm.model_path,
        )

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int,
        model: str,
    ) -> LlmResponse:
        if self._provider == "llamacpp":
            return self._generate_local(prompt, system_prompt, max_tokens, model)
        return self._generate_remote(prompt, system_prompt, max_tokens, model)

    def _generate_remote(
        self, prompt: str, system_prompt: str, max_tokens: int, model: str
    ) -> LlmResponse:
        headers = {"Content-Type": "application/json"}
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        payload = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        }
        try:
            response = self._client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
        except httpx.HTTPError as exc:
            raise DomainError(f"LLM request failed: {exc}") from exc

        if not response.is_success:
            raise DomainError(
                f"LLM endpoint returned {response.status_code}: {response.text}"
            )

        try:
            data = response.json()
            text = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})
            return LlmResponse(
                text=text,
                model=data.get("model", model),
                usage=Usage(
                    input_tokens=int(usage.get("prompt_tokens", 0)),
                    output_tokens=int(usage.get("completion_tokens", 0)),
                ),
            )
        except (KeyError, IndexError, ValueError, TypeError) as exc:
            raise DomainError(f"Malformed LLM response: {exc}") from exc

    def _generate_local(
        self, prompt: str, system_prompt: str, max_tokens: int, model: str
    ) -> LlmResponse:
        try:
            from llama_cpp import Llama
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise DomainError(
                "llama-cpp-python is not installed; install the 'llm' extra"
            ) from exc

        if self._local_model is None:  # pragma: no cover - requires model file
            self._local_model = Llama(model_path=self._model_path)

        result = self._local_model.create_chat_completion(  # pragma: no cover
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
        )
        choice = result["choices"][0]["message"]["content"]  # pragma: no cover
        usage = result.get("usage", {})  # pragma: no cover
        return LlmResponse(  # pragma: no cover
            text=choice,
            model=model,
            usage=Usage(
                input_tokens=int(usage.get("prompt_tokens", 0)),
                output_tokens=int(usage.get("completion_tokens", 0)),
            ),
        )
