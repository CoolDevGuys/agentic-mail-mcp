"""Live write-path smoke test against a real Gmail account.

Opt-in and self-contained: it creates its **own** throwaway message (a draft it
sends to the account's own address), exercises the write tools on it, and
hard-deletes only its own artifacts afterwards. It never touches your existing
mail and never emails a third party.

Run it deliberately:

    GMAIL_MCP_LIVE_WRITE_E2E=1 pytest tests/e2e/test_live_write_path.py -s

Requires an authorized account (``.secrets/token.enc`` via ``gmail-mcp-server
auth``) whose token has the ``gmail.modify`` scope. Skipped otherwise.
"""

from __future__ import annotations

import asyncio
import json
import os
import uuid

import pytest

from src.Bootstrap.Composition import build_oauth_provider, build_use_cases
from src.Bootstrap.Settings import RailguardsConfig, Settings
from src.Gmail.Infrastructure.Google.gmail_api_gateway import GmailApiGateway
from src.MCP.Server import create_server

pytestmark = [pytest.mark.e2e, pytest.mark.uses_real_env]


def _enabled() -> bool:
    if not os.getenv("GMAIL_MCP_LIVE_WRITE_E2E"):
        return False
    provider = build_oauth_provider(Settings.from_env())
    return provider.has_token()


requires_live_write = pytest.mark.skipif(
    not _enabled(),
    reason="set GMAIL_MCP_LIVE_WRITE_E2E=1 and authorize (make auth) to run",
)


def _tool_json(result) -> dict:
    return json.loads(result.content[0].text)


@requires_live_write
async def test_live_write_path() -> None:
    base = Settings.from_env()
    settings = Settings(
        gmail=base.gmail,
        railguards=RailguardsConfig(access_level="read_write"),  # enable writes
    )
    gateway = GmailApiGateway.from_credentials(
        build_oauth_provider(base).load_credentials()
    )
    account = gateway._service.users().getProfile(userId="me").execute()["emailAddress"]
    server = create_server(use_cases=build_use_cases(settings, gateway=gateway), settings=settings)

    async def call(name, args):
        return _tool_json(await server.call_tool(name, args))

    marker = uuid.uuid4().hex[:8]
    subject = f"[MCP-TEST {marker}] delete me"
    to_delete: list[str] = []

    try:
        # 1. create_draft -> send_draft (produces our own test message)
        draft = await call("create_draft", {"to": account, "subject": subject, "body": "write-path test"})
        assert "error" not in draft, draft
        sent = await call("send_draft", {"draft_id": draft["draft_id"]})
        assert "error" not in sent, sent
        msg_id = sent["message_id"]
        to_delete.append(msg_id)
        print(f"\n✓ create_draft + send_draft -> message {msg_id}")

        # allow Gmail a moment to index the sent message
        for _ in range(10):
            got = await call("get_email", {"email_id": msg_id})
            if "error" not in got:
                break
            await asyncio.sleep(1)
        assert "error" not in got, got

        # 2. add_label (system label STARRED is a valid label id)
        labeled = await call("add_label", {"email_id": msg_id, "label": "STARRED"})
        assert labeled == {"status": "labeled", "label": "STARRED"}, labeled
        assert "STARRED" in (await call("get_email", {"email_id": msg_id}))["labels"]
        print("✓ add_label STARRED")

        # 3. forward to self (self only — never a third party)
        fwd = await call("forward_email", {"email_id": msg_id, "to": account})
        assert "error" not in fwd, fwd
        if fwd.get("message_id"):
            to_delete.append(fwd["message_id"])
        print("✓ forward_email (to self)")

        # 4. archive -> INBOX removed
        archived = await call("archive_email", {"email_id": msg_id})
        assert archived == {"status": "archived"}, archived
        assert "INBOX" not in (await call("get_email", {"email_id": msg_id}))["labels"]
        print("✓ archive_email")

        # 5. delete (soft / trash)
        deleted = await call("delete_email", {"email_id": msg_id})
        assert deleted == {"status": "deleted", "permanent": False}, deleted
        assert "TRASH" in (await call("get_email", {"email_id": msg_id}))["labels"]
        print("✓ delete_email (soft/trash)")

        print("\nLIVE WRITE PATH OK ✅")
    finally:
        # Trash our own throwaway artifacts (auto-purges in 30 days). We use
        # trash rather than permanent delete on purpose: permanent
        # `messages.delete` needs the `https://mail.google.com/` scope, which the
        # default `gmail.modify` scope does not grant.
        for mid in to_delete:
            try:
                gateway.trash_message(mid)
            except Exception as exc:  # noqa: BLE001 - best-effort cleanup
                print(f"cleanup: could not trash {mid}: {exc}")
