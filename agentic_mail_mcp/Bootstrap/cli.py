import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from agentic_mail_mcp.Bootstrap.Composition import (
    build_oauth_provider,
    build_resource_context,
    build_use_cases,
    resolve_client_config,
)
from agentic_mail_mcp.Bootstrap.config_init import run_init
from agentic_mail_mcp.Bootstrap.DependencyContainer import Container
from agentic_mail_mcp.Bootstrap.Logging import setup_logging
from agentic_mail_mcp.Bootstrap.Settings import Settings
from agentic_mail_mcp.Common.Domain.Exceptions import DomainError
from agentic_mail_mcp.MCP.Resources import ResourceContext
from agentic_mail_mcp.MCP.Server import create_server, run_server
from agentic_mail_mcp.MCP.Tools.use_cases import McpUseCases


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
            "Missing your Google OAuth client. Point AGENTIC_MAIL_MCP_GMAIL_CLIENT_SECRETS_FILE "
            "at the credentials.json you downloaded from Google Cloud, or set "
            "AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_ID and AGENTIC_MAIL_MCP_GMAIL_OAUTH_CLIENT_SECRET "
            "(see specs/docs/configuration.md — you create your own app).",
            file=sys.stderr,
        )
        sys.exit(1)
    if not gmail.token_encryption_key:
        print(
            "Missing AGENTIC_MAIL_MCP_GMAIL_TOKEN_ENCRYPTION_KEY (any long random string).",
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
        print("Re-run 'agentic-mail-mcp auth' when you're ready.", file=sys.stderr)
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
    print("You can now run 'agentic-mail-mcp' (or restart your MCP client).")


def _load_env_file(path: str) -> None:
    """Load a specific .env file into the environment before Settings are built.

    Values are loaded with ``override=False`` so any variables already set in the
    process environment (e.g. an MCP client's ``env`` block) still win.
    """
    resolved = Path(path).expanduser()
    if not resolved.exists():
        print(f"--env-file not found: {resolved}", file=sys.stderr)
        sys.exit(1)
    load_dotenv(resolved, override=False)


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="agentic-mail-mcp",
        description="Agentic Mail — an MCP server exposing Gmail to AI agents.",
    )
    # Shared across subcommands: for serve/auth it is the file to LOAD config
    # from; for init it is the file to WRITE. Falls back to the
    # AGENTIC_MAIL_MCP_ENV_FILE environment variable.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument(
        "--env-file",
        default=None,
        metavar="PATH",
        help="Path to a .env file (loaded for serve/auth, written for init). "
        "Overrides AGENTIC_MAIL_MCP_ENV_FILE.",
    )

    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("serve", parents=[common], help="Run the MCP server.")
    subparsers.add_parser(
        "auth", parents=[common], help="Authorize access to Gmail (one-time)."
    )
    subparsers.add_parser(
        "init",
        parents=[common],
        help="Interactively generate a .env configuration file.",
    )
    args = parser.parse_args()

    # No subcommand: show help and exit without side effects (never auto-serve).
    if args.command is None:
        parser.print_help()
        return

    env_file = args.env_file or os.environ.get("AGENTIC_MAIL_MCP_ENV_FILE")

    # `init` writes configuration and must run before Settings exist; it does not
    # load Settings or configure logging. --env-file selects the output path.
    if args.command == "init":
        sys.exit(run_init(env_path=Path(env_file) if env_file else Path(".env")))

    # serve/auth: load the requested .env into the environment before Settings
    # are read, so a client-launched server can be pointed at a config file.
    if env_file:
        _load_env_file(env_file)

    settings = Settings.from_env()
    setup_logging(
        level=settings.logging.level,
        json_format=settings.logging.json_format,
    )

    if args.command == "auth":
        _auth(settings)
    else:  # serve
        _serve(settings)


if __name__ == "__main__":
    main()
