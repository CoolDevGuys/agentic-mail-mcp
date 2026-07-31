import asyncio
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from src.Bootstrap.Logging import setup_logging
from src.Bootstrap.Settings import Settings

T = TypeVar("T")


class Container:
    def __init__(self) -> None:
        self._factories: dict[type, Callable] = {}
        self._singletons: dict[type, Any] = {}
        self._async_factories: dict[type, Callable[..., Awaitable[Any]]] = {}

    @classmethod
    def with_defaults(cls, settings: Settings) -> "Container":
        container = cls()
        container.singleton(Settings, settings)
        container.singleton(
            logging.Logger,
            setup_logging(
                level=settings.logging.level,
                json_format=settings.logging.json_format,
            ),
        )
        # DB session factory and event bus are registered here once
        # their implementations land (Phases 2 and 5):
        #   container.register(DBSessionFactory, ...)
        #   container.register(EventBus, ...)
        return container

    def register(
        self,
        interface: type[T],
        factory: Callable[..., T] | Callable[..., Awaitable[T]] | None = None,
        is_async: bool = False,
    ) -> None:
        if factory is None:
            factory = interface

        if is_async:
            self._async_factories[interface] = factory  # type: ignore[assignment]
        else:
            self._factories[interface] = factory

    def singleton(
        self,
        interface: type[T],
        instance: T,
    ) -> None:
        self._singletons[interface] = instance

    async def resolve(self, interface: type[T]) -> T:
        if interface in self._singletons:
            return self._singletons[interface]

        if interface in self._async_factories:
            instance = await self._async_factories[interface]()
            if interface not in self._singletons:
                self._singletons[interface] = instance
            return instance

        if interface in self._factories:
            factory = self._factories[interface]
            instance = factory()
            if asyncio.iscoroutine(instance):
                instance = await instance
            if interface not in self._singletons:
                self._singletons[interface] = instance
            return instance

        raise KeyError(f"No registration found for {interface}")

    def get(self, interface: type[T]) -> T | None:
        return self._singletons.get(interface)
