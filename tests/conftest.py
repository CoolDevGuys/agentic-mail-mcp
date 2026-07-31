from datetime import UTC

import pytest

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import Settings


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
