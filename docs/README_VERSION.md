# Hanuman - README Technique Complet (2025)

## 🧡 Objectif global

**Hanuman** est une API locale d’orchestration personnelle, modulaire, testable et sécurisée, développée en **Python 3.12** avec **FastAPI**, destinée à interfacer des services tiers (GitHub, Notion, OpenAI...) avec des scripts et données locales. Sa philosophie repose sur un design **scalable**, **entierèrement testé**, **loggé proprement**, **lisible**, **typé**, et **configurable à tous les niveaux**.

---

## 🔄 Arborescence

```bash
hanuman/
├── .env                         # Secrets/API tokens (non versionné)
├── Makefile                     # Commandes d’automatisation
├── pyproject.toml               # Configuration Poetry + outils
├── poetry.lock                  # Verrouillage des dépendances
├── .gitignore                   # Fichiers exclus du repo
├── .semgrep.yml                 # Règles de sécurité/statique
├── coverage.xml                 # Rapport de couverture XML (Codecov)
├── logs/
│   └── hanuman.log              # Log unique consolidé
├── src/
│   ├── hanuman/
│   │   ├── main.py             # Entrée principale FastAPI
│   │   ├── api/               # Routes REST regroupées par domaine
│   │   ├── core/              # Logging, sécurité, config
│   │   ├── services/          # Logique fonctionnelle (traitement)
│   │   ├── models/            # Pydantic (si besoin)
│   │   └── utils/             # Helpers (log, décorateurs...)
├── tests/
│   ├── __init__.py
│   ├── test_status.py
│   ├── test_log_trace_endpoint.py
│   ├── services/
│   │   ├── test_calendar_ping.py
│   │   ├── test_chess_ping.py
│   │   ├── test_github_ping.py
│   │   ├── test_notion_ping.py
│   │   ├── test_openai_ping.py
│   │   ├── test_obsidian_ping.py
│   │   └── test_wikipedia_ping.py
│   └── conftest.py          # Fixtures partagées
```

---

## ✨ Points techniques clés

### 🚀 API FastAPI

* Point d’entrée : `main.py`
* Routes dynamiquement importées via `include_router()`
* Middleware d’audit (`log_requests`) actif sur toutes les routes

### 🔧 Logging structlog

* Logging unifié avec **structlog 25.4**
* Configuration centralisée dans `core/logging.py`
* Logs formatés : timestamp, module, niveau, message enrichi (requête, IP...)
* Fichier unique `logs/hanuman.log`, rotation future prévue

### 🌐 Sécurité

* Variables d’environnement via `.env` chargé manuellement
* `token_manager.py` pour gestion de tokens dynamiques (non finalisé)
* Clés sensibles ignorées via `.gitignore`

### 🔬 Analyse statique

* Formatage : **Black**, ligne 100
* Lint : **Ruff** (E, F, I), ignore E501 (lignes longues)
* Typage strict via **mypy** (activé dans `pyproject.toml`)
* Sécurité : **Semgrep** avec catégories `security`, `structure`, `style`

### 🔮 Tests professionnels

* Framework : **pytest** avec **pytest-cov**
* Rapport de couverture **HTML** et **XML** pour Codecov
* `Makefile` avec cibles `test`, `test-cov`, `coverage-html`, `clean`
* Arborescence des tests par module, un `ping` par service
* Convention de réponse testée : `{ "ok": true|false, "error"?: str }`

### 🏆 Intégration continue (CI)

* GitHub Actions actif
* Codecov badge affiché
* Préparation d’un système robuste d’échecs tolérés à terme

---

## 🛠️ Makefile (extraits)

```make
run:              # uvicorn reload auto
	poetry run uvicorn src.hanuman.main:app --reload

lint:             # Analyse lint (Ruff)
	poetry run ruff check .

format:           # Format avec black
	poetry run black .

clean:            # Supprime .pyc et cache tests
	rm -rf .pytest_cache __pycache__ */__pycache__ *.pyc

clean-logs:
	rm -f logs/*.log

test:
	poetry run pytest

test-cov:
	poetry run pytest --cov=src/ --cov-report=xml

coverage-html:
	poetry run pytest --cov=src/ --cov-report=html
	xdg-open htmlcov/index.html || open htmlcov/index.html || true
```

---

## 🔢 Services disponibles

| Service   | Fichier route      | Fichier service                 | Token ? |
| --------- | ------------------ | ------------------------------- | ------- |
| Status    | `api/status.py`    | —                               | Non     |
| Notion    | `api/notion.py`    | `services/notion_service.py`    | Oui     |
| GitHub    | `api/github.py`    | `services/github_service.py`    | Oui     |
| Chess.com | `api/chess_com.py` | `services/chess_service.py`     | Non     |
| Obsidian  | `api/obsidian.py`  | `services/obsidian_service.py`  | Non     |
| OpenAI    | `api/openai.py`    | `services/openai_service.py`    | Oui     |
| Calendar  | `api/calendar.py`  | `services/calendar_service.py`  | Oui     |
| Wikipedia | `api/wikipedia.py` | `services/wikipedia_service.py` | Non     |

---

## 🔝 Qualité actuelle

| Domaine             | État                          |
| ------------------- | ----------------------------- |
| Logging             | Structlog 100% opérationnel   |
| Typage              | Mypy strict                   |
| Lint / Format       | Black + Ruff                  |
| Sécurité statique   | Semgrep personnalisé          |
| Tests unitaires     | 100% ping testés              |
| Couverture globale  | > 81% (hors fichiers mineurs) |
| CI GitHub           | Fonctionnelle                 |
| Convention de tests | Unifiée ok/error + JSON       |
| Codebase            | Propre, modulaire, claire     |

---

## 📄 Fichiers critiques (paths absolus utiles)

* `src/hanuman/main.py` : point d’entrée
* `logs/hanuman.log` : log consolidé
* `tests/` : tous les tests organisés par service
* `htmlcov/index.html` : rapport HTML local de couverture
* `.env` : variables sensibles (gitignored)
* `Makefile` : automatisation locale
* `pyproject.toml` : référence centrale de la config (toolchain)

---

## 🛠️ Prochaines idées (hors scope README)

* Déploiement Docker (en local)
* Organisation d’une CLI `hanuman`
* Ajout de workers asynchrones
* Intégration progressive de business logic utile

---

▶️ Ce fichier est généré manuellement, ne pas le remplacer par le README.md original. Il constitue une référence technique interne pour les versions en cours.
