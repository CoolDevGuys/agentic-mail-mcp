import pytest

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Settings import Settings


class TestContainer:
    @pytest.mark.asyncio
    async def test_register_and_resolve(self):
        container = Container()

        class Service:
            pass

        container.register(Service)
        instance = await container.resolve(Service)
        assert isinstance(instance, Service)

    @pytest.mark.asyncio
    async def test_register_with_factory(self):
        container = Container()

        class Service:
            def __init__(self, value: str):
                self.value = value

        container.register(Service, lambda: Service("test"))
        instance = await container.resolve(Service)
        assert instance.value == "test"

    @pytest.mark.asyncio
    async def test_singleton(self):
        container = Container()
        settings = Settings()

        container.singleton(Settings, settings)
        instance1 = await container.resolve(Settings)
        instance2 = await container.resolve(Settings)

        assert instance1 is instance2
        assert instance1 is settings

    @pytest.mark.asyncio
    async def test_resolve_raises_for_unknown(self):
        container = Container()

        class Unknown:
            pass

        with pytest.raises(KeyError, match="No registration found for"):
            await container.resolve(Unknown)

    def test_get_returns_none_for_unknown(self):
        container = Container()

        class Unknown:
            pass

        assert container.get(Unknown) is None

    def test_get_returns_singleton(self):
        container = Container()
        settings = Settings()

        container.singleton(Settings, settings)
        assert container.get(Settings) is settings

    @pytest.mark.asyncio
    async def test_async_factory(self):
        container = Container()

        class AsyncService:
            def __init__(self):
                self.value = "async"

        async def factory():
            return AsyncService()

        container.register(AsyncService, factory, is_async=True)

        instance = await container.resolve(AsyncService)
        assert isinstance(instance, AsyncService)
        assert instance.value == "async"

    @pytest.mark.asyncio
    async def test_factory_resolves_sync(self):
        container = Container()

        class Service:
            def __init__(self):
                self.value = "sync"

        container.register(Service, lambda: Service())

        instance = await container.resolve(Service)
        assert isinstance(instance, Service)
        assert instance.value == "sync"

    def test_with_defaults(self):
        settings = Settings()
        container = Container.with_defaults(settings)

        assert container.get(Settings) is settings
        assert container.get(__import__("logging").Logger) is not None

    @pytest.mark.asyncio
    async def test_singleton_takes_precedence_over_factory(self):
        container = Container()

        class Service:
            pass

        singleton_instance = Service()
        container.singleton(Service, singleton_instance)
        container.register(Service, lambda: Service())

        instance = await container.resolve(Service)
        assert instance is singleton_instance
