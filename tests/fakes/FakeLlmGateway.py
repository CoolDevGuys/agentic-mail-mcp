class FakeLlmGateway:
    def __init__(self) -> None:
        self._calls: list[dict] = []

    async def generate(self, prompt: str, **kwargs) -> str:
        self._calls.append({"prompt": prompt, "kwargs": kwargs})
        return f"Response to: {prompt[:50]}"

    def get_calls(self) -> list[dict]:
        return self._calls
