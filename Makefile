# =====================================================
# Hanuman Makefile
# =====================================================

SHELL := /bin/bash

POETRY := poetry
RUN := $(POETRY) run

API_APP ?= hanuman.main:app
HOST ?= 127.0.0.1
PORT ?= 8000
COVERAGE_MIN ?= 90

.DEFAULT_GOAL := help

.PHONY: \
	help install update \
	format format-check lint lint-fix typecheck \
	test coverage coverage-html \
	semgrep audit security \
	check all-check \
	run run-api stop clean

# -----------------------------------------------------
# Aide
# -----------------------------------------------------

help: ## Affiche les commandes disponibles
	@echo ""
	@echo "Hanuman — commandes disponibles"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?##"}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'
	@echo ""

# -----------------------------------------------------
# Dépendances
# -----------------------------------------------------

install: ## Installe les dépendances du projet
	$(POETRY) install

update: ## Met à jour les dépendances et le fichier poetry.lock
	$(POETRY) update

# -----------------------------------------------------
# Formatage et qualité
# -----------------------------------------------------

format: ## Corrige automatiquement le formatage et les erreurs Ruff réparables
	$(RUN) black .
	$(RUN) ruff check . --fix

format-check: ## Vérifie le formatage sans modifier les fichiers
	$(RUN) black --check .

lint: ## Vérifie le code avec Ruff sans le modifier
	$(RUN) ruff check .

lint-fix: ## Corrige automatiquement les erreurs Ruff réparables
	$(RUN) ruff check . --fix

typecheck: ## Vérifie le typage avec mypy
	$(RUN) mypy src/hanuman tests

# -----------------------------------------------------
# Tests et couverture
# -----------------------------------------------------

test: ## Lance toute la suite de tests
	$(RUN) pytest -q

coverage: ## Lance tous les tests avec couverture et seuil minimal
	$(RUN) coverage erase
	$(RUN) coverage run -m pytest -q
	$(RUN) coverage report -m --fail-under=$(COVERAGE_MIN)
	$(RUN) coverage xml

coverage-html: ## Génère le rapport HTML de couverture
	$(RUN) coverage erase
	$(RUN) coverage run -m pytest -q
	$(RUN) coverage html
	@echo "Rapport HTML : file://$(PWD)/htmlcov/index.html"

# -----------------------------------------------------
# Sécurité
# -----------------------------------------------------

semgrep: ## Analyse statique de sécurité avec Semgrep
	$(RUN) semgrep --config p/ci .

audit: ## Audite les dépendances Python avec pip-audit
	$(RUN) pip-audit

security: semgrep ## Lance tous les contrôles de sécurité

# -----------------------------------------------------
# Vérifications globales
# -----------------------------------------------------

check: format-check lint typecheck test ## Vérifie formatage, lint, typage et tests

all-check: ## Lance absolument toutes les vérifications locales
	@echo ""
	@echo "=== Hanuman : vérification complète ==="
	@echo ""
	@echo "[1/6] Black"
	$(RUN) black --check .
	@echo ""
	@echo "[2/6] Ruff"
	$(RUN) ruff check .
	@echo ""
	@echo "[3/6] mypy"
	$(RUN) mypy src/hanuman tests
	@echo ""
	@echo "[4/6] Tests + couverture"
	$(RUN) coverage erase
	$(RUN) coverage run -m pytest -q
	$(RUN) coverage report -m --fail-under=$(COVERAGE_MIN)
	$(RUN) coverage xml
	@echo ""
	@echo "[5/6] Semgrep"
	$(RUN) semgrep --config p/ci .
	
	@echo ""
	@echo "=== Toutes les vérifications ont réussi ==="

# -----------------------------------------------------
# Exécution
# -----------------------------------------------------

run-api: ## Lance l'API FastAPI en mode développement
	PYTHONPATH=src $(RUN) uvicorn $(API_APP) \
		--reload \
		--host $(HOST) \
		--port $(PORT)

run: run-api ## Alias de run-api

stop: ## Arrête le serveur Uvicorn de Hanuman
	@pkill -f "uvicorn .*hanuman\.main:app" || true

# -----------------------------------------------------
# Nettoyage
# -----------------------------------------------------

clean: ## Supprime caches, rapports et fichiers temporaires
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache
	@rm -rf htmlcov coverage.xml .coverage
	@echo "Nettoyage terminé."
