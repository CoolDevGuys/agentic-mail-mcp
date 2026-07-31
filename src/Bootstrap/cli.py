import argparse
import asyncio
import sys

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Lifespan import lifespan
from src.Bootstrap.Logging import setup_logging
from src.Bootstrap.Settings import Settings


async def run_server() -> None:
    settings = Settings.from_env()
    setup_logging(
        level=settings.logging.level,
        json_format=settings.logging.json_format,
    )

    container = Container()
    container.singleton(Settings, settings)

    async with lifespan(container):
        print("Server running...")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(prog="gmail-mcp-server")
    parser.parse_args()

    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
