from agentic_mail_mcp.Common.Domain.Specifications import (
    AndSpecification,
    NotSpecification,
    OrSpecification,
    Specification,
)


class _IsEven(Specification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate % 2 == 0


class _IsPositive(Specification[int]):
    def is_satisfied_by(self, candidate: int) -> bool:
        return candidate > 0


class TestSpecificationBase:
    def test_concrete_satisfied(self) -> None:
        spec = _IsEven()
        assert spec.is_satisfied_by(4) is True

    def test_concrete_not_satisfied(self) -> None:
        spec = _IsEven()
        assert spec.is_satisfied_by(3) is False


class TestAndSpecification:
    def test_both_satisfied(self) -> None:
        spec = AndSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(4) is True

    def test_left_not_satisfied(self) -> None:
        spec = AndSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(3) is False

    def test_right_not_satisfied(self) -> None:
        spec = AndSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(-2) is False


class TestOrSpecification:
    def test_left_satisfied(self) -> None:
        spec = OrSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(4) is True

    def test_right_satisfied(self) -> None:
        spec = OrSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(3) is True

    def test_neither_satisfied(self) -> None:
        spec = OrSpecification(_IsEven(), _IsPositive())
        assert spec.is_satisfied_by(-3) is False


class TestNotSpecification:
    def test_negation(self) -> None:
        spec = NotSpecification(_IsEven())
        assert spec.is_satisfied_by(3) is True

    def test_double_negation(self) -> None:
        spec = NotSpecification(NotSpecification(_IsEven()))
        assert spec.is_satisfied_by(4) is True


class TestChainedComposition:
    def test_and_or_not_chained(self) -> None:
        spec = AndSpecification(
            OrSpecification(_IsEven(), _IsPositive()),
            NotSpecification(_IsPositive()),
        )
        assert spec.is_satisfied_by(-2) is True
        assert spec.is_satisfied_by(3) is False
        assert spec.is_satisfied_by(4) is False
        assert spec.is_satisfied_by(-3) is False

    def test_fluent_api(self) -> None:
        spec = _IsEven().and_(_IsPositive())
        assert spec.is_satisfied_by(4) is True
        assert spec.is_satisfied_by(3) is False
        assert spec.is_satisfied_by(-2) is False
