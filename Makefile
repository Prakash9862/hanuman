# ⚙️ Makefile — commandes utilitaires pour Hanuman

.PHONY: run test lint format clean

# 🟢 Lancer l'API en mode développement
run:
	poetry run uvicorn src.hanuman.main:app --reload

# 🧪 Lancer tous les tests
test:
	poetry run pytest -v tests/

# 🎨 Formater le code (Black)
format:
	poetry run black src tests

# 🧹 Linter (Flake8)
lint:
	poetry run flake8 src tests

# 🧼 Nettoyer les fichiers inutiles
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
