from src.Common.Domain.ValueObjects.uuid_id import UUIDId
from src.Common.Infrastructure.IdGenerator import UuidIdGenerator


class TestUuidIdGenerator:
    def test_returns_uuid_id(self) -> None:
        gen = UuidIdGenerator()
        result = gen.generate()
        assert isinstance(result, UUIDId)

    def test_uniqueness(self) -> None:
        gen = UuidIdGenerator()
        id1 = gen.generate()
        id2 = gen.generate()
        assert id1 != id2

    def test_type_correctness(self) -> None:
        gen = UuidIdGenerator()
        result = gen.generate()
        assert type(result).__name__ == "UUIDId"
