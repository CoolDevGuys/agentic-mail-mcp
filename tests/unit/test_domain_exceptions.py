from src.Common.Domain.Exceptions import (
    ConcurrencyError,
    DomainError,
    NotFoundError,
    PermissionError,
    ValidationError,
)


class TestDomainError:
    def test_message(self) -> None:
        err = DomainError("something failed")
        assert str(err) == "something failed"
        assert err.message == "something failed"

    def test_context_default(self) -> None:
        err = DomainError("failed")
        assert err.context == {}

    def test_context_provided(self) -> None:
        err = DomainError("failed", context={"key": "val"})
        assert err.context == {"key": "val"}

    def test_inherits_exception(self) -> None:
        assert issubclass(DomainError, Exception)


class TestValidationError:
    def test_inherits_domain_error(self) -> None:
        assert issubclass(ValidationError, DomainError)

    def test_message_and_context(self) -> None:
        err = ValidationError("invalid", context={"field": "email"})
        assert str(err) == "invalid"
        assert err.context == {"field": "email"}


class TestNotFoundError:
    def test_inherits_domain_error(self) -> None:
        assert issubclass(NotFoundError, DomainError)

    def test_with_context(self) -> None:
        err = NotFoundError("not found", context={"entity_id": "123"})
        assert err.context["entity_id"] == "123"


class TestPermissionError:
    def test_inherits_domain_error(self) -> None:
        assert issubclass(PermissionError, DomainError)

    def test_with_context(self) -> None:
        err = PermissionError("denied", context={"action": "delete"})
        assert err.context["action"] == "delete"


class TestConcurrencyError:
    def test_inherits_domain_error(self) -> None:
        assert issubclass(ConcurrencyError, DomainError)

    def test_message(self) -> None:
        err = ConcurrencyError("conflict")
        assert str(err) == "conflict"
