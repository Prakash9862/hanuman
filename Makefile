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
	@echo "[1/5] Black"
	$(RUN) black --check .
	@echo ""
	@echo "[2/5] Ruff"
	$(RUN) ruff check .
	@echo ""
	@echo "[3/5] mypy"
	$(RUN) mypy src/hanuman tests
	@echo ""
	@echo "[4/5] Tests + couverture"
	$(RUN) coverage erase
	$(RUN) coverage run -m pytest -q
	$(RUN) coverage report -m --fail-under=$(COVERAGE_MIN)
	$(RUN) coverage xml
	@echo ""
	@echo "[5/5] Semgrep"
	$(RUN) semgrep --config p/ci .
	@echo ""
	@echo "=== Toutes les vérifications ont réussi ==="

# -----------------------------------------------------
# Exécution
# -----------------------------------------------------

BACKEND_PID := .hanuman-backend.pid
FRONTEND_PID := .hanuman-frontend.pid
BACKEND_LOG := .hanuman-backend.log
FRONTEND_LOG := .hanuman-frontend.log
HANUMAN_URL := http://127.0.0.1:5173

run: ## Lance backend, frontend et ouvre Hanuman
	@$(MAKE) stop >/dev/null 2>&1 || true
	@echo "Démarrage du backend..."
	@nohup env PYTHONPATH=src $(RUN) uvicorn $(API_APP) \
		--reload \
		--host $(HOST) \
		--port $(PORT) \
		> $(BACKEND_LOG) 2>&1 & echo $$! > $(BACKEND_PID)
	@echo "Démarrage du frontend..."
	@nohup npm --prefix frontend run dev -- --host 127.0.0.1 \
		> $(FRONTEND_LOG) 2>&1 & echo $$! > $(FRONTEND_PID)
	@echo "Attente de Hanuman..."
	@for i in $$(seq 1 30); do \
		if curl -fsS $(HANUMAN_URL) >/dev/null 2>&1; then \
			xdg-open $(HANUMAN_URL) >/dev/null 2>&1 & \
			echo "Hanuman est lancé : $(HANUMAN_URL)"; \
			exit 0; \
		fi; \
		sleep 1; \
	done; \
	echo "Le frontend n'a pas démarré. Consulte $(FRONTEND_LOG)"; \
	exit 1

stop: ## Arrête backend et tous les serveurs Vite de Hanuman
	@echo "Arrêt de Hanuman..."
	@if [ -f $(BACKEND_PID) ]; then \
		kill $$(cat $(BACKEND_PID)) 2>/dev/null || true; \
		rm -f $(BACKEND_PID); \
	fi
	@if [ -f $(FRONTEND_PID) ]; then \
		kill $$(cat $(FRONTEND_PID)) 2>/dev/null || true; \
		rm -f $(FRONTEND_PID); \
	fi
	@pkill -f "uvicorn .*hanuman\.main:app" 2>/dev/null || true
	@pkill -f "node .*frontend/node_modules/.bin/vite" 2>/dev/null || true
	@pkill -f "vite.*--host 127\.0\.0\.1" 2>/dev/null || true
	@echo "Hanuman arrêté."

restart: stop ## Redémarre Hanuman
	@sleep 1
	@$(MAKE) run

# -----------------------------------------------------
# Nettoyage
# -----------------------------------------------------

clean: ## Supprime caches, rapports et fichiers temporaires
	@find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	@rm -rf .pytest_cache .mypy_cache .ruff_cache
	@rm -rf htmlcov coverage.xml .coverage
	@echo "Nettoyage terminé."
