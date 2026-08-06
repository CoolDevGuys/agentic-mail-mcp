from __future__ import annotations

import dataclasses

import pytest

from agentic_mail_mcp.Common.Domain.Exceptions import ValidationError
from agentic_mail_mcp.Intelligence.Domain.ValueObjects import (
    ModelConfig,
    PromptTemplate,
)


class TestPromptTemplate:
    def test_render_with_all_variables(self) -> None:
        template = PromptTemplate(
            name="summary",
            template="Summarize: {text} in {language}",
        )

        result = template.render(text="Hello world", language="English")

        assert result == "Summarize: Hello world in English"

    def test_render_with_extra_variables(self) -> None:
        template = PromptTemplate(
            name="greet",
            template="Hello {name}",
        )

        result = template.render(name="Alex", extra="ignored")

        assert result == "Hello Alex"

    def test_render_missing_variable_raises(self) -> None:
        template = PromptTemplate(
            name="greet",
            template="Hello {name}",
        )

        with pytest.raises(ValidationError, match="Missing required variables"):
            template.render()

    def test_render_missing_multiple_variables(self) -> None:
        template = PromptTemplate(
            name="summary",
            template="Summarize: {text} in {language}",
        )

        with pytest.raises(ValidationError, match="Missing required variables"):
            template.render(text="Hello")

    def test_render_no_variables(self) -> None:
        template = PromptTemplate(
            name="static",
            template="Hello world",
        )

        assert template.render() == "Hello world"

    def test_equality(self) -> None:
        t1 = PromptTemplate(name="greet", template="Hello {name}")
        t2 = PromptTemplate(name="greet", template="Hello {name}")

        assert t1 == t2

    def test_inequality_different_template(self) -> None:
        t1 = PromptTemplate(name="greet", template="Hello {name}")
        t2 = PromptTemplate(name="greet", template="Hi {name}")

        assert t1 != t2

    def test_hashable(self) -> None:
        t1 = PromptTemplate(name="greet", template="Hello {name}")
        t2 = PromptTemplate(name="greet", template="Hello {name}")

        assert hash(t1) == hash(t2)
        assert {t1, t2} == {t1}


class TestModelConfig:
    def test_create_valid_config(self) -> None:
        config = ModelConfig(
            provider="openai",
            model_id="gpt-4",
            max_tokens=1024,
            temperature=0.7,
        )

        assert config.provider == "openai"
        assert config.model_id == "gpt-4"
        assert config.max_tokens == 1024
        assert config.temperature == 0.7

    def test_max_tokens_zero_raises(self) -> None:
        with pytest.raises(ValidationError, match="max_tokens must be > 0"):
            ModelConfig(
                provider="openai",
                model_id="gpt-4",
                max_tokens=0,
                temperature=0.7,
            )

    def test_max_tokens_negative_raises(self) -> None:
        with pytest.raises(ValidationError, match="max_tokens must be > 0"):
            ModelConfig(
                provider="openai",
                model_id="gpt-4",
                max_tokens=-1,
                temperature=0.7,
            )

    def test_temperature_below_range_raises(self) -> None:
        with pytest.raises(
            ValidationError, match="temperature must be between 0.0 and 1.0"
        ):
            ModelConfig(
                provider="openai",
                model_id="gpt-4",
                max_tokens=1024,
                temperature=-0.1,
            )

    def test_temperature_above_range_raises(self) -> None:
        with pytest.raises(
            ValidationError, match="temperature must be between 0.0 and 1.0"
        ):
            ModelConfig(
                provider="openai",
                model_id="gpt-4",
                max_tokens=1024,
                temperature=1.5,
            )

    def test_boundary_temperature_values(self) -> None:
        for temp in (0.0, 1.0):
            config = ModelConfig(
                provider="openai",
                model_id="gpt-4",
                max_tokens=1,
                temperature=temp,
            )
            assert config.temperature == temp

    def test_equality(self) -> None:
        c1 = ModelConfig("openai", "gpt-4", 1024, 0.7)
        c2 = ModelConfig("openai", "gpt-4", 1024, 0.7)

        assert c1 == c2

    def test_inequality_different_model(self) -> None:
        c1 = ModelConfig("openai", "gpt-4", 1024, 0.7)
        c2 = ModelConfig("openai", "gpt-3.5", 1024, 0.7)

        assert c1 != c2

    def test_frozen(self) -> None:
        config = ModelConfig("openai", "gpt-4", 1024, 0.7)

        with pytest.raises(dataclasses.FrozenInstanceError):
            config.provider = "anthropic"  # type: ignore
