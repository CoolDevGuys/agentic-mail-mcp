import pytest

from agentic_mail_mcp.Bootstrap.Lifespan import lifespan


class TestLifespan:
    @pytest.mark.asyncio
    async def test_lifespan_yields_state(self):
        state = None

        async with lifespan(None) as s:
            state = s

        assert state is not None
        assert "settings" in state

    @pytest.mark.asyncio
    async def test_lifespan_provides_settings(self):
        async with lifespan(None) as state:
            from agentic_mail_mcp.Bootstrap.Settings import Settings

            assert isinstance(state["settings"], Settings)

    @pytest.mark.asyncio
    async def test_lifespan_calls_startup_and_shutdown(self):
        startup_called = []
        shutdown_called = []

        import agentic_mail_mcp.Bootstrap.Lifespan as lifespan_module

        original_startup = lifespan_module._startup
        original_shutdown = lifespan_module._shutdown

        async def track_startup(settings):
            startup_called.append(True)
            await original_startup(settings)

        async def track_shutdown(settings):
            shutdown_called.append(True)
            await original_shutdown(settings)

        lifespan_module._startup = track_startup
        lifespan_module._shutdown = track_shutdown

        try:
            async with lifespan(None):
                pass

            assert len(startup_called) == 1
            assert len(shutdown_called) == 1
        finally:
            lifespan_module._startup = original_startup
            lifespan_module._shutdown = original_shutdown
