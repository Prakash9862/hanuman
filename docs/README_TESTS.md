# 📦 Système de test Hanuman (version v2.4)

Ce document décrit l'intégralité du système de test en place pour le projet Hanuman à la version `v2.4`. Il fournit une vue d'ensemble technique, sans projection future, uniquement basée sur l'état réel du système.

---

## 📁 Structure des tests

Le projet utilise `pytest` comme moteur de test, avec une organisation modulaire claire :

```bash
hanuman/
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   └── ...
│   ├── api/
│   │   ├── test_log_trace_endpoint.py
│   │   └── ...
│   ├── services/
│   │   ├── test_calendar_ping.py
│   │   ├── test_chess_ping.py
│   │   ├── test_github_ping.py
│   │   ├── test_notion_ping.py
│   │   ├── test_obsidian_ping.py
│   │   ├── test_openai_ping.py
│   │   └── test_wikipedia_ping.py
```

Chaque sous-dossier contient uniquement des tests correspondant à sa couche :

- `unit/` : fonctions internes isolées
- `api/` : endpoints FastAPI
- `services/` : accès à des services externes (Google, Chess, Notion, etc.)

---

## 🧪 Moteur de test : `pytest`

Tous les tests sont écrits en Python pur avec `pytest`.

- Le fichier `tests/conftest.py` expose deux fixtures :

  - `client()` : instance de `TestClient(FastAPI)` pour tests HTTP
  - `headers()` : dictionnaire contenant l'entête d'authentification

---

## 📈 Couverture et rapports

Le projet utilise `pytest-cov` pour mesurer la couverture de code :

- Rapport XML : `coverage.xml` (utilisé par Codecov en CI)
- Rapport HTML local : `htmlcov/index.html`

Ces fichiers sont générés automatiquement via le Makefile.

---

## 🛠️ Makefile : commandes de test

Les commandes suivantes sont disponibles pour exécuter les tests :

```makefile
test:
	poetry run pytest tests/

test-cov:
	poetry run pytest tests/ --cov=src/hanuman --cov-report=xml

coverage-html:
	poetry run pytest tests/ --cov=src/hanuman --cov-report=html --cov-report=term-missing
	@xdg-open htmlcov/index.html || open htmlcov/index.html || start htmlcov/index.html

clean-coverage:
	rm -rf .coverage htmlcov coverage.xml
```

- `make test` : exécute tous les tests
- `make test-cov` : exécute les tests et produit `coverage.xml`
- `make coverage-html` : produit un rapport visuel dans `htmlcov/`
- `make clean-coverage` : supprime tous les fichiers de couverture

---

## 🧪 Liste des tests en place (v2.4)

### 📂 `tests/services/`

| Fichier                  | Fonction          | Ce que ça teste                           |
| ------------------------ | ----------------- | ----------------------------------------- |
| `test_calendar_ping.py`  | `/calendar/ping`  | Source = "calendar", int `calendar_count` |
| `test_chess_ping.py`     | `/chess/ping`     | Source = "chess", str `username`          |
| `test_github_ping.py`    | `/github/ping`    | Source = "github", str `login`            |
| `test_notion_ping.py`    | `/notion/ping`    | Source = "notion", dict `user`            |
| `test_obsidian_ping.py`  | `/obsidian/ping`  | Source = "obsidian", int `note_count`     |
| `test_openai_ping.py`    | `/openai/ping`    | Source = "openai", int `model_count`      |
| `test_wikipedia_ping.py` | `/wikipedia/ping` | Source = "wikipedia", title = "openai"    |

### 📂 `tests/api/`

| Fichier                      | Fonction  | Ce que ça teste                                       |
| ---------------------------- | --------- | ----------------------------------------------------- |
| `test_log_trace_endpoint.py` | `/status` | Logs structlog : "Requête reçue", "Exécution réussie" |

---

## 📦 Couverture CI / GitHub Actions

- Le fichier `coverage.xml` est lu par Codecov.
- Un badge Codecov est affiché dans le `README.md` principal.
- Tous les tests sont compatibles CI (aucun test cassant, aucune variable d'environnement manquante).

---

## 📁 Dossiers présents dans `tests/`

- `__init__.py` est présent dans tous les sous-dossiers pour garantir la compatibilité d'import.
- Aucun mock avancé n'est encore en place (pas de `pytest-mock`, pas de `unittest.mock`).
- Pas de `@pytest.mark.skipif`, car tous les tests passent en l'état.

---

## ✅ Statut actuel (v2.4)

| Aspect                 | Statut                                 |
| ---------------------- | -------------------------------------- |
| Organisation des tests | ✅ Stable, modulaire                   |
| Couverture à jour      | ✅ HTML + XML + badge CI               |
| Intégration CI         | ✅ Compatible GitHub Actions + Codecov |
| Tests critiques        | ✅ Ping, statut, logs                  |
| Robustesse globale     | ✅ Aucun test cassant en l'état        |

Le système de test Hanuman est donc **opérationnel, stable et proprement documenté** à la version `v2.4`.
