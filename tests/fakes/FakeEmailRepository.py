class FakeEmailRepository:
    def __init__(self) -> None:
        self._emails: dict[str, dict] = {}

    def add(self, email_id: str, email: dict) -> None:
        self._emails[email_id] = email

    def get(self, email_id: str) -> dict | None:
        return self._emails.get(email_id)

    def list(self) -> list[dict]:
        return list(self._emails.values())

    def delete(self, email_id: str) -> bool:
        if email_id in self._emails:
            del self._emails[email_id]
            return True
        return False

    def count(self) -> int:
        return len(self._emails)
