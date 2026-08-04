# Releasing

Maintainer guide for publishing the package to PyPI and the image to a registry.
Both are deliberate, human-run steps performed after a release is tagged.

## Prerequisites

- A clean working tree on the release commit, all tests green.
- `pip install build twine` for PyPI; Docker with `buildx` for the image.
- API tokens: a Test-PyPI token and a production PyPI token; registry credentials.

## PyPI

1. **Bump the version** in `pyproject.toml` (`project.version`) and add a
   `CHANGELOG.md` entry.

2. **Build** the distributions:

   ```bash
   rm -rf dist
   python -m build
   ```

   This produces a wheel and a source distribution in `dist/`.

3. **Check** the metadata renders and is valid:

   ```bash
   python -m twine check dist/*
   ```

4. **Publish to Test-PyPI first** and install from there to smoke-test:

   ```bash
   python -m twine upload --repository testpypi dist/*
   pip install --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ gmail-mcp-server
   gmail-mcp-server --help
   ```

5. **Publish to production PyPI** once Test-PyPI looks correct:

   ```bash
   python -m twine upload dist/*
   ```

## Docker image (multi-arch)

The `Dockerfile` is architecture-agnostic; build for both common architectures
with `buildx`:

```bash
docker buildx create --use --name gmail-mcp-builder   # once
docker buildx build \
  --platform linux/amd64,linux/arm64 \
  --tag <registry>/gmail-mcp-server:<version> \
  --tag <registry>/gmail-mcp-server:latest \
  --push .
```

The container's health check assumes HTTP transport
(`GMAIL_MCP_MCP_TRANSPORT=http`); a stdio container is a foreground process
whose liveness is the process itself.
