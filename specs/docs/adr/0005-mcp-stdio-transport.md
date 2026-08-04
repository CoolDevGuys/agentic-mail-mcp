# 0005 — MCP stdio as the Default Transport

Status: accepted

Context: The server's primary consumer is an AI agent harness (Claude Desktop, IDE agents, and similar), not a browser or a public API client. MCP defines multiple transports — stdio and streamable HTTP. We must pick a default that matches how the server is actually launched and keeps the common case zero-configuration and secure.

Decision: **stdio is the default transport; HTTP is opt-in** via `Settings.mcp.transport`. Agent harnesses launch the server as a child process and speak MCP over stdin/stdout, so stdio needs no ports, no bind address, and no network exposure — the transport is the process pipe. HTTP (streamable) is available for shared, always-on deployments and is selected with `GMAIL_MCP_MCP_TRANSPORT=http` plus `host`/`port`. The transport choice is isolated in `MCP/Server.py` (`run_server`); tools, resources, and prompts are transport-agnostic.

Consequences:

- **Easier:** The default launch is a single command with no networking to configure or secure, which is exactly what agent harnesses expect. No open port means no accidental network exposure of a mailbox-mutating server. Local development and the packaged console entry point work out of the box.
- **Harder:** A stdio process has no port to health-check; container/liveness checks apply to the HTTP mode. Multiple concurrent clients need the HTTP transport, so shared deployments must opt in and then take on the usual network-security concerns.
- **Future:** Additional transports can be added behind the same `transport` setting without touching tool code. If remote deployments become common, HTTP hardening (auth, TLS termination) can be layered on top of the existing opt-in.
