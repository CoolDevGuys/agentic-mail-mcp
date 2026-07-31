from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ValueObject:
    """Base class for value objects with structural equality, hashing, and repr."""

    def __eq__(self, other: object) -> bool:
        if type(other) is not type(self):
            return False
        return self._get_values() == other._get_values()

    def __hash__(self) -> int:
        return hash(self._get_hash_key())

    def __repr__(self) -> str:
        fields = ", ".join(f"{k}={v!r}" for k, v in self._get_values().items())
        return f"{type(self).__name__}({fields})"

    def _get_values(self) -> dict[str, Any]:
        return {
            k: getattr(self, k)
            for k in self.__dataclass_fields__  # type: ignore[attr-defined]
        }

    def _get_hash_key(self) -> tuple:
        return tuple(self._get_values().values())
