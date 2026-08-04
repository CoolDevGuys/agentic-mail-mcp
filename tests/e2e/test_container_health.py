"""Container startup + health-check smoke test (Phase 8.8).

Builds the image, starts the container in HTTP-transport mode, and waits for the
Docker health check to report ``healthy``. Skipped when Docker is unavailable;
also opt-in (set ``GMAIL_MCP_DOCKER_E2E=1``) so the default suite stays fast and
does not build an image on every run.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import time
import uuid

import pytest

pytestmark = pytest.mark.e2e

_IMAGE = "gmail-mcp-server:e2e-health"


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    return subprocess.run(
        ["docker", "info"], capture_output=True, text=True, check=False
    ).returncode == 0


requires_docker = pytest.mark.skipif(
    not os.getenv("GMAIL_MCP_DOCKER_E2E") or not _docker_available(),
    reason="Docker not available or GMAIL_MCP_DOCKER_E2E not set",
)


def _run(args: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True, check=False, **kw)


@requires_docker
def test_container_starts_and_reports_healthy() -> None:
    repo_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    build = _run(["docker", "build", "-t", _IMAGE, repo_root])
    assert build.returncode == 0, build.stderr

    name = f"gmail-mcp-e2e-{uuid.uuid4().hex[:8]}"
    run = _run(
        [
            "docker", "run", "-d", "--name", name,
            "-e", "GMAIL_MCP_MCP_TRANSPORT=http",
            "-e", "GMAIL_MCP_MCP_HOST=0.0.0.0",
            "-e", "GMAIL_MCP_MCP_PORT=8080",
            _IMAGE,
        ]
    )
    assert run.returncode == 0, run.stderr

    try:
        status = "starting"
        deadline = time.time() + 90
        while time.time() < deadline:
            inspect = _run(
                ["docker", "inspect", "--format", "{{json .State.Health.Status}}", name]
            )
            status = json.loads(inspect.stdout.strip() or '"unknown"')
            if status == "healthy":
                break
            if status == "unhealthy":
                logs = _run(["docker", "logs", name]).stdout
                pytest.fail(f"container became unhealthy:\n{logs}")
            time.sleep(3)
        assert status == "healthy", f"container never became healthy (last: {status})"
    finally:
        _run(["docker", "rm", "-f", name])
