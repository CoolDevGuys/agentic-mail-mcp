from datetime import UTC

import pytest

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import (
    DatabaseConfig,
    GmailConfig,
    LLMConfig,
    LoggingConfig,
    MCPConfig,
    NotificationsConfig,
    RailguardsConfig,
    SearchConfig,
    Settings,
)

# Every settings class (parent + sections) reads a `.env` file by default. Tests
# must be deterministic regardless of a developer's local `.env` (created by
# `make env`), so we disable `.env` loading for the whole test session. Env-var
# based tests use `monkeypatch.setenv`, which sets `os.environ` and is unaffected.
_SETTINGS_CLASSES = (
    Settings,
    GmailConfig,
    DatabaseConfig,
    RailguardsConfig,
    MCPConfig,
    LLMConfig,
    SearchConfig,
    NotificationsConfig,
    LoggingConfig,
)


@pytest.fixture(autouse=True)
def _isolate_settings_from_dotenv(monkeypatch):
    for cls in _SETTINGS_CLASSES:
        monkeypatch.setitem(cls.model_config, "env_file", None)


@pytest.fixture
def settings() -> Settings:
    return Settings.from_env()


@pytest.fixture
def event_bus():
    events = []

    class EventBus:
        def publish(self, event):
            events.append(event)

        def subscribe(self, event_type, handler):
            pass

        def get_events(self):
            return events

    return EventBus()


@pytest.fixture
def clock():
    from datetime import datetime

    class Clock:
        def now(self):
            return datetime.now(UTC)

    return Clock()


@pytest.fixture
def container(settings) -> Container:
    return Container.with_defaults(settings)
