import argparse
import sys

from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Logging import setup_logging
from src.Bootstrap.Settings import Settings
from src.MCP.Server import create_server, run_server


def main() -> None:
    parser = argparse.ArgumentParser(prog="gmail-mcp-server")
    parser.parse_args()

    settings = Settings.from_env()
    setup_logging(
        level=settings.logging.level,
        json_format=settings.logging.json_format,
    )

    container = Container.with_defaults(settings)
    # The composition root registers an ``McpUseCases`` (and ``ResourceContext``)
    # singleton on the container; create_server picks them up and registers the
    # matching tools and resources. Without them the server still starts with its
    # prompts and any registered resources.
    server = create_server(container)

    try:
        run_server(server, settings)
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
