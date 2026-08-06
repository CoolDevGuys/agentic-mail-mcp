import argparse
import sys

from src.Bootstrap.Composition import (
    build_oauth_provider,
    build_resource_context,
    build_use_cases,
    resolve_client_config,
)
from src.Bootstrap.DependencyContainer import Container
from src.Bootstrap.Logging import setup_logging
from src.Bootstrap.Settings import Settings
from src.Common.Domain.Exceptions import DomainError
from src.MCP.Resources import ResourceContext
from src.MCP.Server import create_server, run_server
from src.MCP.Tools.use_cases import McpUseCases


def _serve(settings: Settings) -> None:
    container = Container.with_defaults(settings)
    # Composition root: build the real use cases and resources and register them
    # so create_server exposes the Gmail tools.
    container.singleton(McpUseCases, build_use_cases(settings))
    container.singleton(ResourceContext, build_resource_context(settings))

    server = create_server(container)
    try:
        run_server(server, settings)
    except KeyboardInterrupt:
        sys.exit(0)


def _auth(settings: Settings) -> None:
    gmail = settings.gmail
    if resolve_client_config(settings) is None:
        print(
            "Missing your Google OAuth client. Point GMAIL_MCP_GMAIL_CLIENT_SECRETS_FILE "
            "at the credentials.json you downloaded from Google Cloud, or set "
            "GMAIL_MCP_GMAIL_OAUTH_CLIENT_ID and GMAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET "
            "(see specs/docs/configuration.md — you create your own app).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not gmail.token_encryption_key:
        print(
            "Missing GMAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY (any long random string).",
            file=sys.stderr,
        )
        sys.exit(1)

    provider = build_oauth_provider(settings)
    print("Opening a browser to authorize access to your Gmail account…")
    print("Sign in with a test-user account and click Allow. Press Ctrl+C to cancel.")
    try:
        provider.authorize_interactive()
    except KeyboardInterrupt:
        print("\n⚠️  Authorization canceled — no token was saved.", file=sys.stderr)
        print("Re-run 'gmail-mcp-server auth' when you're ready.", file=sys.stderr)
        sys.exit(1)
    except DomainError as exc:
        print(f"\n⚠️  {exc}", file=sys.stderr)
        print(
            "If the consent screen showed 'access blocked', add your account "
            "under 'Test users' on the OAuth consent screen "
            "(see specs/docs/configuration.md).",
            file=sys.stderr,
        )
        sys.exit(1)
    print(f"✅ Authorized. Encrypted token stored at {gmail.token_storage_path}.")
    print("You can now run 'gmail-mcp-server' (or restart your MCP client).")


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="gmail-mcp-server",
        description="Gmail MCP server for AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("serve", help="Run the MCP server (default).")
    subparsers.add_parser("auth", help="Authorize access to Gmail (one-time).")
    args = parser.parse_args()

    settings = Settings.from_env()
    setup_logging(
        level=settings.logging.level,
        json_format=settings.logging.json_format,
    )

    if args.command == "auth":
        _auth(settings)
    else:
        _serve(settings)


if __name__ == "__main__":
    main()
