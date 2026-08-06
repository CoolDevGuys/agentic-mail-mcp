import uuid
from dataclasses import dataclass

from agentic_mail_mcp.Common.Domain.ValueObjects.base import ValueObject
from agentic_mail_mcp.Common.Domain.ValueObjects.uuid_id import UUIDId


@dataclass(frozen=True)
class _TestVO(ValueObject):
    a: int
    b: str


class TestValueObjectEquality:
    def test_equal_values(self) -> None:
        assert _TestVO(a=1, b="x") == _TestVO(a=1, b="x")

    def test_different_values(self) -> None:
        assert _TestVO(a=1, b="x") != _TestVO(a=2, b="x")

    def test_different_type(self) -> None:
        assert _TestVO(a=1, b="x") != "not a value object"

    def test_all_fields_compared(self) -> None:
        assert _TestVO(a=1, b="x") != _TestVO(a=1, b="y")


class TestValueObjectHash:
    def test_equal_objects_same_hash(self) -> None:
        v1 = _TestVO(a=1, b="x")
        v2 = _TestVO(a=1, b="x")
        assert hash(v1) == hash(v2)

    def test_usable_in_set(self) -> None:
        s = {_TestVO(a=1, b="x"), _TestVO(a=1, b="x")}
        assert len(s) == 1

    def test_usable_in_dict_key(self) -> None:
        d = {_TestVO(a=1, b="x"): "val"}
        assert d[_TestVO(a=1, b="x")] == "val"


class TestValueObjectRepr:
    def test_repr_includes_class_and_fields(self) -> None:
        r = repr(_TestVO(a=1, b="x"))
        assert "_TestVO" in r
        assert "a=1" in r
        assert "b='x'" in r


class TestUUIDId:
    def test_generate_returns_uuid_id(self) -> None:
        uid = UUIDId.generate()
        assert isinstance(uid, UUIDId)

    def test_generate_uniqueness(self) -> None:
        uid1 = UUIDId.generate()
        uid2 = UUIDId.generate()
        assert uid1 != uid2

    def test_same_uuid_equal(self) -> None:
        u = uuid.uuid4()
        uid1 = UUIDId.from_uuid(u)
        uid2 = UUIDId.from_uuid(u)
        assert uid1 == uid2
        assert hash(uid1) == hash(uid2)

    def test_from_string(self) -> None:
        u = uuid.uuid4()
        uid = UUIDId.from_string(str(u))
        assert str(uid) == str(u)

    def test_str_conversion(self) -> None:
        u = uuid.uuid4()
        uid = UUIDId.from_uuid(u)
        assert str(uid) == str(u)

    def test_repr(self) -> None:
        u = uuid.uuid4()
        uid = UUIDId.from_uuid(u)
        assert "UUIDId" in repr(uid)
