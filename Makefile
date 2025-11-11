.RECIPEPREFIX := >
SHELL := /bin/bash
.ONESHELL:
.SHELLFLAGS := -euo pipefail -c

POETRY ?= $(shell command -v poetry 2>/dev/null)
RUN     := $(POETRY) run
SRC     := src/hanuman
TESTS   := tests

help: ## Affiche l’aide
> awk 'BEGIN{FS":.*##";print "\nCibles :\n"} /^[A-Za-z0-9_.-]+:.*##/ {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2} END{print ""}' $(MAKEFILE_LIST)

install: ## Installe les dépendances
> $(POETRY) install

fmt: ## Format
> $(RUN) ruff format . || true

lint: ## Lint
> $(RUN) ruff check . --fix || true

type: ## Type-check
> $(RUN) mypy $(SRC) $(TESTS)

test: ## Tests
> $(RUN) pytest -q

coverage: ## Couverture
> $(RUN) pytest --cov=$(SRC) --cov-report=term-missing --cov-report=xml:coverage.xml

check: fmt lint type test ## Tout-en-un

run: ## Lance l’API
> [ -f .env ] && set -a && source .env && set +a || true
> $(RUN) uvicorn hanuman.api.main:app --reload --host 127.0.0.1 --port $${PORT:-8000}

clean: ## Nettoyage
> find . -type d -name "__pycache__" -exec rm -rf {} + || true
> rm -rf .pytest_cache .mypy_cache htmlcov coverage.xml .coverage || true

