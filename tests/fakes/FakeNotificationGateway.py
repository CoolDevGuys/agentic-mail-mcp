class FakeNotificationGateway:
    def __init__(self) -> None:
        self._notifications: list[dict] = []

    async def send(self, event_type: str, data: dict) -> None:
        self._notifications.append({"event_type": event_type, "data": data})

    async def publish(self, topic: str, message: dict) -> None:
        self._notifications.append({"topic": topic, "message": message})

    def get_notifications(self) -> list[dict]:
        return self._notifications

    def count(self) -> int:
        return len(self._notifications)
