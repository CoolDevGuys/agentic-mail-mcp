from typing import Any


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Any] = {}

    def register(self, name: str, tool: Any) -> None:
        self._tools[name] = tool

    def get(self, name: str) -> Any | None:
        return self._tools.get(name)

    def list(self) -> list[str]:
        return list(self._tools.keys())
