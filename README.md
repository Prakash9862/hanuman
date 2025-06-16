# Hanuman

[![CI](https://github.com/Prakash9862/hanuman/actions/workflows/test.yml/badge.svg)](https://github.com/Prakash9862/hanuman/actions)
[![Coverage](https://codecov.io/gh/Prakash9862/hanuman/branch/main/graph/badge.svg)](https://app.codecov.io/gh/Prakash9862/hanuman)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Poetry](https://img.shields.io/badge/poetry-enabled-brightgreen)
![FastAPI](https://img.shields.io/badge/fastapi-2025-green)

## Description

API locale modulaire pour l’orchestration de services distants et de scripts locaux. Projet organisé, typé, testé, avec journalisation centralisée.

## Spécifications

* Python 3.12+
* FastAPI (serveur ASGI)
* Uvicorn (local only)
* Pydantic v2 (strict mode)
* Couverture de tests vérifiée via Codecov
* CI GitHub Actions (tests, lint, typecheck)

## Structure

```
hanuman/
├── .github/workflows/         # GitHub Actions (test.yml)
├── .env                       # Variables d’environnement locales
├── Makefile                   # Commandes (run, test, format, lint)
├── pyproject.toml             # Config unique (poetry, lint, mypy, deps)
├── logs/                      # Logs runtime (debug + error)
├── config/                    # Config centralisée YAML/JSON
├── src/hanuman/               # Code principal (api, core, services, models)
│   ├── main.py                # Entrée FastAPI
│   ├── api/                   # Endpoints FastAPI regroupés
│   ├── core/                  # Config, loggers, sécurité
│   ├── services/              # Intégrations (Notion, GitHub, etc.)
│   ├── models/                # Schémas Pydantic
│   └── utils/                 # Fonctions auxiliaires
├── tests/                     # Tests unitaires
├── coverage.xml               # Rapport couverture (Codecov)
└── README.md                  # Ce fichier
```

## Makefile

```makefile
make run         # Lance Uvicorn avec reload
make test        # Exécute tous les tests Pytest
make test-cov    # Tests avec couverture + XML (Codecov)
make lint        # Lint via Ruff
make typecheck   # Analyse Mypy stricte
make format      # Format via Black
make clean       # Supprime caches Python
```

## Couverture de test

* Pytest avec `pytest-cov`
* Rapport XML : `coverage.xml`
* Affichage des lignes manquantes dans la console
* Codecov actif sur branche `main`

## CI

* GitHub Actions
* Déclenché sur `push` et `pull_request`
* Steps : install, lint, format, typecheck, tests, coverage
* Upload auto vers Codecov.io

## Logging

* `logs/hanuman.log` : niveau DEBUG+
* `logs/hanuman_error.log` : erreurs structurées JSON
* Config : `config/logging.yaml`

## API

* FastAPI avec endpoints regroupés dans `api/`
* Ping endpoints : `/status`, `/notion/ping`, `/github/ping`, etc.
* Swagger (`/docs`) et Redoc (`/redoc`) actifs
* Modèles typés avec `PingResult`, etc.

## Services intégrés

| Service         | Route           | Token .env         | Testé |
| --------------- | --------------- | ------------------ | ----- |
| Status          | /status         | non                | oui   |
| Notion          | /notion/ping    | NOTION\_TOKEN      | oui   |
| GitHub          | /github/ping    | GITHUB\_TOKEN      | oui   |
| Chess.com       | /chess/ping     | non                | oui   |
| Obsidian        | /obsidian/ping  | non                | oui   |
| OpenAI          | /openai/ping    | OPENAI\_TOKEN      | oui   |
| Wikipedia       | /wikipedia/ping | non                | oui   |
| Google Calendar | /calendar/ping  | OAUTH\_JSON + .env | oui   |

## Typage

* Pydantic v2 (strict, model\_dump, model\_validate)
* Mypy niveau strict (aucun Any toléré)
* CI échoue si mypy n’est pas propre

## Sécurité

* Auth par token statique JWT (dans .env)
* Aucun port exposé publiquement
* Secrets non versionnés (`.env`, `secrets/`)
* Code scanné via Ruff + tests de type + Codecov

## Prochaine étape

* Modules `/run/` pour scripts et commandes
* Dockerisation locale
* Ajout SQLite / JSON pour mémoire locale
* Interface Web ou CLI minimale (optionnelle)

## Notes internes

* Vault Obsidian : `/home/prakash/Prakash/obsidian/Privé`
* Arborescence respectée (src/hanuman)
* Couverture cible : 80 % minimum
* Toutes les dépendances déclarées dans `pyproject.toml`
