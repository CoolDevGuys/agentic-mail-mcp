class FakeGmailGateway:
    def __init__(self) -> None:
        self._messages: list[dict] = []
        self._watched = False

    async def list_messages(self, query: str = "", max_results: int = 100) -> list[dict]:
        return self._messages[:max_results]

    async def get_message(self, message_id: str) -> dict | None:
        for msg in self._messages:
            if msg.get("id") == message_id:
                return msg
        return None

    async def send_message(self, raw: str) -> dict:
        msg = {"id": f"fake-{len(self._messages) + 1}", "raw": raw}
        self._messages.append(msg)
        return msg

    async def watch(self, webhook_url: str) -> None:
        self._watched = True

    async def unwatch(self) -> None:
        self._watched = False

    def add_message(self, msg: dict) -> None:
        self._messages.append(msg)
