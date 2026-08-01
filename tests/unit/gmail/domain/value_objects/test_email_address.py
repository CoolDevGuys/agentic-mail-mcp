
import pytest

from src.Common.Domain.Exceptions import ValidationError
from src.Gmail.Domain.ValueObjects.email_address import EmailAddress
from src.Gmail.Domain.ValueObjects.gmail_query import GmailQuery


class TestEmailAddressCreation:
    def test_valid_simple_email(self) -> None:
        email = EmailAddress(value="user@example.com")
        assert email.value == "user@example.com"

    def test_valid_email_with_numbers(self) -> None:
        email = EmailAddress(value="user123@example456.com")
        assert email.value == "user123@example456.com"

    def test_valid_email_with_special_chars(self) -> None:
        email = EmailAddress(value="user.name+tag@domain.co.uk")
        assert email.value == "user.name+tag@domain.co.uk"

    def test_local_part_property(self) -> None:
        email = EmailAddress(value="john.doe@example.com")
        assert email.local_part == "john.doe"

    def test_domain_property(self) -> None:
        email = EmailAddress(value="john.doe@example.com")
        assert email.domain == "example.com"

    def test_local_part_and_domain_split(self) -> None:
        email = EmailAddress(value="user+tag@sub.domain.com")
        assert email.local_part == "user+tag"
        assert email.domain == "sub.domain.com"


class TestEmailAddressValidation:
    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="")

    def test_rejects_missing_at_sign(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="userexample.com")

    def test_rejects_at_sign_only(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="@")

    def test_rejects_multiple_at_signs(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="user@@example.com")

    def test_rejects_at_at_start(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="@example.com")

    def test_rejects_at_at_end(self) -> None:
        with pytest.raises(ValidationError):
            EmailAddress(value="user@")

    def test_rejects_exceeds_254_characters(self) -> None:
        long_email = "a" * 253 + "@x.com"
        with pytest.raises(ValidationError):
            EmailAddress(value=long_email)

    def test_accepts_254_characters(self) -> None:
        exact_email = "a" * 248 + "@x.com"
        email = EmailAddress(value=exact_email)
        assert len(email.value) == 254


class TestEmailAddressEdgeCases:
    def test_plus_addressing(self) -> None:
        email = EmailAddress(value="user+tag@example.com")
        assert email.local_part == "user+tag"
        assert email.domain == "example.com"

    def test_subdomain(self) -> None:
        email = EmailAddress(value="user@mail.sub.example.com")
        assert email.domain == "mail.sub.example.com"

    def test_dots_in_local_part(self) -> None:
        email = EmailAddress(value="first.last@example.com")
        assert email.local_part == "first.last"

    def test_single_char_local_and_domain(self) -> None:
        email = EmailAddress(value="a@b.co")
        assert email.local_part == "a"
        assert email.domain == "b.co"

    def test_hyphen_in_domain(self) -> None:
        email = EmailAddress(value="user@my-domain.com")
        assert email.domain == "my-domain.com"

    def test_plus_addressing_multiple_tags(self) -> None:
        email = EmailAddress(value="user+tag1+tag2@example.com")
        assert email.local_part == "user+tag1+tag2"


class TestEmailAddressEquality:
    def test_same_value_equals(self) -> None:
        e1 = EmailAddress(value="user@example.com")
        e2 = EmailAddress(value="user@example.com")
        assert e1 == e2

    def test_different_values_not_equal(self) -> None:
        e1 = EmailAddress(value="user1@example.com")
        e2 = EmailAddress(value="user2@example.com")
        assert e1 != e2

    def test_not_equal_to_string(self) -> None:
        email = EmailAddress(value="user@example.com")
        assert email != "user@example.com"

    def test_not_equal_to_other_vo_type(self) -> None:
        email = EmailAddress(value="user@example.com")
        query = GmailQuery(value="user@example.com")
        assert email != query

    def test_equal_hashes(self) -> None:
        e1 = EmailAddress(value="user@example.com")
        e2 = EmailAddress(value="user@example.com")
        assert hash(e1) == hash(e2)

    def test_usable_in_set(self) -> None:
        s = {
            EmailAddress(value="a@example.com"),
            EmailAddress(value="a@example.com"),
        }
        assert len(s) == 1
