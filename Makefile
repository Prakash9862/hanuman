# ⚙️ Makefile — commandes utilitaires pour Hanuman

.PHONY: run test lint format clean

# Lancer l'API en mode développement
run:
	uvicorn src.hanuman.main:app --reload

# Lancer tous les tests
test:
	pytest -v tests/

# Formatter le code (Black)
format:
	black src tests

# Linter (Flake8)
lint:
	flake8 src tests

# Nettoyer les fichiers inutiles
clean:
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
