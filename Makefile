# Agentic Mail MCP — developer tasks.
# Run `make` or `make help` to list available targets.

# Tooling is run from a local virtualenv (.venv) so commands are reproducible.
# Override with e.g. `make PYTHON=python3.11 install` or `make VENV=env test`.
PYTHON ?= python3
VENV   ?= .venv
BIN    := $(VENV)/bin
PY     := $(BIN)/python
PIP    := $(BIN)/pip

# Marker file: lets other targets depend on "the venv exists with deps".
STAMP  := $(VENV)/.install.stamp

.DEFAULT_GOAL := help

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------

.PHONY: help
help: ## Show this help
	@echo "Agentic Mail MCP — make targets:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-16s\033[0m %s\n", $$1, $$2}'

$(VENV):
	$(PYTHON) -m venv $(VENV)

.PHONY: install
install: $(STAMP) ## Create the venv and install the package with dev extras (editable)
$(STAMP): pyproject.toml | $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev]"
	@touch $(STAMP)

.PHONY: install-all
install-all: | $(VENV) ## Install with every optional extra (postgresql, search, notifications, llm)
	$(PIP) install --upgrade pip
	$(PIP) install -e ".[dev,postgresql,search,notifications,llm]"
	@touch $(STAMP)

.PHONY: env
env: ## Create a local .env from .env.example (if missing)
	@if [ -f .env ]; then \
		echo ".env already exists — leaving it untouched"; \
	else \
		cp .env.example .env && echo "Created .env from .env.example — fill in the secrets"; \
	fi

.PHONY: init
init: $(STAMP) ## Generate .env interactively (guided config wizard)
	$(BIN)/agentic-mail-mcp init

.PHONY: setup
setup: install env migrate ## First-time setup: venv + deps + .env + database schema
	@echo "Setup complete. Run 'make run' to start the server."

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

.PHONY: auth
auth: $(STAMP) ## Authorize Gmail access (one-time browser consent)
	$(BIN)/agentic-mail-mcp auth

.PHONY: run
run: $(STAMP) ## Run the MCP server (stdio transport)
	$(BIN)/agentic-mail-mcp serve

.PHONY: run-http
run-http: $(STAMP) ## Run the MCP server over HTTP (host/port from Settings)
	AGENTIC_MAIL_MCP_MCP_TRANSPORT=http $(BIN)/agentic-mail-mcp serve

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

.PHONY: test
test: $(STAMP) ## Run the full test suite with coverage gates (as CI does)
	$(BIN)/pytest

.PHONY: test-quick
test-quick: $(STAMP) ## Run tests fast: no coverage, stop on first failure
	$(BIN)/pytest --no-cov -q -x

.PHONY: test-e2e
test-e2e: $(STAMP) ## Run end-to-end tests, including the opt-in Docker container test
	AGENTIC_MAIL_MCP_DOCKER_E2E=1 $(BIN)/pytest tests/e2e --no-cov

.PHONY: cov
cov: $(STAMP) ## Run tests and print a coverage report
	$(BIN)/pytest --cov-report=term-missing

# ---------------------------------------------------------------------------
# Quality gates
# ---------------------------------------------------------------------------

.PHONY: lint
lint: $(STAMP) ## Lint with ruff (no changes)
	$(BIN)/ruff check agentic_mail_mcp tests

.PHONY: format
format: $(STAMP) ## Auto-format and fix imports with ruff
	$(BIN)/ruff check --fix agentic_mail_mcp tests
	$(BIN)/ruff format agentic_mail_mcp tests

.PHONY: typecheck
typecheck: $(STAMP) ## Type-check with mypy
	$(BIN)/mypy agentic_mail_mcp

.PHONY: check
check: lint typecheck test ## Run every quality gate (lint + types + tests)

# ---------------------------------------------------------------------------
# Database migrations (Alembic)
# ---------------------------------------------------------------------------

.PHONY: migrate
migrate: $(STAMP) ## Apply all pending migrations (upgrade to head)
	$(BIN)/alembic upgrade head

.PHONY: migration
migration: $(STAMP) ## Autogenerate a migration: make migration m="describe change"
	@if [ -z "$(m)" ]; then echo "Usage: make migration m=\"describe change\""; exit 1; fi
	$(BIN)/alembic revision --autogenerate -m "$(m)"

.PHONY: downgrade
downgrade: $(STAMP) ## Roll back the last migration
	$(BIN)/alembic downgrade -1

.PHONY: migrate-history
migrate-history: $(STAMP) ## Show migration history and current revision
	$(BIN)/alembic history --indicate-current

# ---------------------------------------------------------------------------
# Packaging & Docker
# ---------------------------------------------------------------------------

.PHONY: build
build: $(STAMP) ## Build the sdist + wheel and validate metadata
	rm -rf dist
	$(PY) -m build
	$(PY) -m twine check dist/*

.PHONY: docker-build
docker-build: ## Build the Docker image
	docker build -t agentic-mail-mcp:local .

.PHONY: docker-up
docker-up: ## Start the stack via docker-compose (server + optional postgres)
	docker compose up --build

.PHONY: docker-down
docker-down: ## Stop and remove the docker-compose stack
	docker compose down

# ---------------------------------------------------------------------------
# Housekeeping
# ---------------------------------------------------------------------------

.PHONY: clean
clean: ## Remove build artifacts, caches, and coverage data
	rm -rf dist build *.egg-info agentic_mail_mcp/*.egg-info
	rm -rf .pytest_cache .ruff_cache .mypy_cache .coverage htmlcov
	find . -type d -name __pycache__ -not -path "./.venv/*" -exec rm -rf {} + 2>/dev/null || true

.PHONY: distclean
distclean: clean ## clean + remove the virtualenv
	rm -rf $(VENV)
