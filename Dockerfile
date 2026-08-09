# syntax=docker/dockerfile:1

# --- Builder stage: build a wheel from the source tree ---
FROM python:3.11-slim AS builder

WORKDIR /build

RUN pip install --no-cache-dir build

# Copy the sources needed to build the distribution.
COPY pyproject.toml README.md LICENSE ./
COPY agentic_mail_mcp/ agentic_mail_mcp/

RUN python -m build --wheel --outdir /dist

# --- Runtime stage: install only the built wheel, no build toolchain ---
FROM python:3.11-slim AS runtime

WORKDIR /app

# Install pysqlite3-binary for SQLite extension loading support (needed by sqlite-vec).
# The slim image's system SQLite is compiled without SQLITE_ENABLE_LOAD_EXTENSION.
RUN pip install --no-cache-dir pysqlite3-binary

# Install the package (and its dependencies) from the wheel produced above.
COPY --from=builder /dist/*.whl /tmp/
RUN pip install --no-cache-dir "/tmp/*.whl[search]" && rm -rf /tmp/*.whl

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser
USER appuser

# Health check applies to HTTP transport (AGENTIC_MAIL_MCP_MCP_TRANSPORT=http); a stdio
# container is a foreground process whose liveness is the process itself.
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; s=socket.socket(); s.settimeout(5); s.connect((os.getenv('AGENTIC_MAIL_MCP_MCP_HOST','127.0.0.1'), int(os.getenv('AGENTIC_MAIL_MCP_MCP_PORT','8080')))); s.close()" || exit 1

CMD ["agentic-mail-mcp", "serve"]
