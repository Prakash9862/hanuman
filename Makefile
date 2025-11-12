# =====================================================
# Hanuman Makefile (propre, tabs corrigés)
# =====================================================
SHELL := /bin/bash

POETRY       := $(shell command -v poetry 2>/dev/null)
RUN          := $(POETRY) run
API_APP      ?= hanuman.main:app
HOST         ?= 127.0.0.1
PORT         ?= 8000

.PHONY: help
help:
	@echo "Cibles disponibles :"
	@grep -E '^[a-zA-Z_-]+:.*?##' Makefile | awk 'BEGIN{FS=":.*?##"}{printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

# -----------------------------------------------------
# Commandes principales
# -----------------------------------------------------
install: ## Installe les dépendances
	$(POETRY) install

fmt: ## Formate le code
	$(RUN) ruff format . || true

lint: ## Corrige les warnings
	$(RUN) ruff check . --fix || true

test: ## Lance les tests
	$(RUN) pytest -q

check: fmt lint test ## Tout-en-un

run-api: ## Lance l'API Hanuman
	PYTHONPATH=src $(RUN) uvicorn $(API_APP) --reload --host $(HOST) --port $(PORT)

run: run-api ## Alias pratique

clean: ## Nettoyage
	@find . -type d -name "__pycache__" -exec rm -rf {} + || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + || true
	@rm -rf htmlcov coverage.xml .coverage || true

.type: ;


.PHONY: check
check: fmt lint typecheck test  ## Tout-en-un

.PHONY: typecheck
.PHONY: check
check: fmt lint typecheck test  ## Tout-en-un

.PHONY: stop
stop:
	@pkill -f "uvicorn .*hanuman\.main:app" || true
.PHONY: typecheck
typecheck:  ## mypy
	$(RUN) mypy src/hanuman tests
