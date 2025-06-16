Données générales

# 📘 Hanuman — README Technique Global

## 📁 Structure

```
hanuman/
├── .github/workflows/         # GitHub Actions (lint, tests, CI)
│   └── test.yml
├── .env                       # Variables d’environnement (tokens, secrets)
├── Makefile                   # Raccourcis de commande (run, lint, test, clean…)
├── pyproject.toml             # Config unique (poetry, black, mypy, flake8…)
├── logs/
│   ├── hanuman.log            # Log principal DEBUG
│   └── hanuman_error.log      # Log JSON niveau ERROR
├── config/
│   └── logging.yaml           # Configuration centralisée des logs
├── src/hanuman/
│   ├── main.py                # Entrée FastAPI (inclut tous les routers)
│   ├── api/                   # Définition des routes (/notion/ping, etc.)
│   ├── core/                  # Fonctions transverses : logging, token, env
│   ├── services/              # Logique métier de chaque intégration
│   └── utils/                 # Décorateurs, helpers, modèles Pydantic
├── tests/                     # Tests Pytest de chaque ping
└── README.md                  # Ce fichier
```

## 🔄 Intégrations (modules actifs)

| Service         | API Route         | Fichier API    | Fichier service        | Token `.env`          |
| --------------- | ----------------- | -------------- | ---------------------- | --------------------- |
| Status          | `/status`         | `status.py`    | —                      | ❌                     |
| Notion          | `/notion/ping`    | `notion.py`    | `notion_service.py`    | ✅ `NOTION_TOKEN`      |
| GitHub          | `/github/ping`    | `github.py`    | `github_service.py`    | ✅ `GITHUB_TOKEN`      |
| Chess.com       | `/chess/ping`     | `chess_com.py` | `chess_service.py`     | ❌                     |
| Obsidian        | `/obsidian/ping`  | `obsidian.py`  | `obsidian_service.py`  | ❌                     |
| OpenAI          | `/openai/ping`    | `openai.py`    | `openai_service.py`    | ✅ `OPENAI_TOKEN`      |
| Wikipedia       | `/wikipedia/ping` | `wikipedia.py` | `wikipedia_service.py` | ❌                     |
| Google Calendar | `/calendar/ping`  | `calendar.py`  | `calendar_service.py`  | ✅ OAuth JSON + `.env` |

## 🧪 Tests unitaires

Tous les `tests/test_*_ping.py` valident le bon fonctionnement des endpoints `/ping` associés.
Logique :

* `"ok": true` → vérifie les clés utiles (ex: login, note\_count…)
* `"ok": false` → vérifie la présence de `"error"`
* Log automatique via décorateur `@log_ping`

Commandes :

```bash
make test       # Lancement de tous les tests
make lint       # Lint avec flake8
make typecheck  # Analyse de type avec mypy
```

## 🧱 Outils et qualité

* **Poetry** : gestionnaire de dépendances (dev, lock, build)
* **Flake8** : linting (défini dans `pyproject.toml`)
* **Black** : formateur (auto-formatage)
* **Mypy** : typage strict (progressif, coverage en cours)
* **Bandit** : sécurité de base (optionnel)

```bash
make format     # Black
make security   # Bandit
```

## 🚀 GitHub Actions (CI)

* `test.yml` déclenché sur :

  * `push` sur `main`, `v2*`
  * `pull_request` vers `main`
* Étapes :

  * Checkout
  * Setup Python (3.12)
  * Install deps avec Poetry
  * Lint (flake8)
  * Format (black --check)
  * Typecheck (mypy)
  * Tests (`pytest`)

## 🧠 Convention & Décorateurs

* Ping centralisé avec `@log_ping` (logs, temps d’exec, réponse standardisée)
* Modèle `PingResult` (Pydantic) uniforme pour tous les retours JSON
* Routes `/docs` (Swagger) et `/redoc` actives par défaut

## 📌 Récap global

| État            | Valeur         |
| --------------- | -------------- |
| Routes Ping     | ✅ 8 / 8        |
| Tests Pytest    | ✅ tous OK      |
| Logging central | ✅ actif        |
| Typage Mypy     | ⚠️ partiel     |
| CI GitHub       | ✅ opérationnel |

## 🔜 Suivi version

* v2.x : API modulaire, loggée, testée, CI en place
* v3.0 (prévue) :

  * Ajout scripts internes
  * Authentification OAuth avancée
  * Sécurité renforcée
  * Orchestration de tâches complexes

---

Ce fichier est la référence technique de **Hanuman**.
Il est destiné à structurer et suivre tous les composants actifs du projet.
  
---

# 🛣️ Roadmap Hanuman — Objectif v3.0

## 🧭 Vision stratégique

> Hanuman est une API personnelle de supervision et d’automatisation multi-système, conçue pour orchestrer les flux entre services web, scripts locaux, stockage personnel et assistants cognitifs. Son but est de constituer une plateforme unifiée, personnelle mais professionnelle, capable d’agir, de mémoriser, de sécuriser et d’évoluer.

Hanuman repose sur des standards de production : FastAPI, OAuth2, logs structurés, versionnement Git, typage strict, modularité des services. L’objectif est de développer un outil puissant, maintenable, scalable, capable de se déployer à long terme sur différentes machines (ThinkPad, VPS, mobile). Chaque évolution s’inscrit dans une logique de maîtrise technique totale.

---

## ✅ Historique des versions

### `v1.0` – Initialisation

* Mise en place du projet : structure `src/hanuman/`, `Makefile`, `.env`, `pyproject.toml`
* Logging centralisé (`logging.yaml`, JSON erreurs)
* Tests unitaires avec `pytest`
* Organisation en `api/`, `services/`, `core/`

### `v2.0` – Intégration modulaire des services

* Connexions validées avec : Notion, GitHub, OpenAI, Obsidian (local), Chess.com, Wikipedia
* Authentification OAuth2 fonctionnelle pour Google Calendar
* Services testés via `/ping`, vérification des tokens, logs dédiés
* Gestion multi-module via `main.py`, routing FastAPI automatique
* Premiers tags Git (`v1.0`, `v2.0`) et dashboard GitHub à jour

---

## 🎯 Objectif de la v3.0

> Créer un **noyau autonome, sécurisé et opérationnel**, capable d’exécuter des commandes internes, de stocker des états locaux, de sécuriser les accès et de préparer l’ouverture vers une UI ou des assistants.

La version 3.0 **ne déclenchera pas encore les grandes automatisations**, mais posera **tous les fondements pour que cela devienne simple, propre, maintenable et sécurisé**.

### Critères fondamentaux de la v3.0 :

* ✅ Gestion centralisée des tokens (OAuth2, static) via `token_manager`
* ✅ Authentification interne par JWT (statique pour v3.0)
* ✅ Possibilité d’exécuter des scripts ou commandes via `/run/`
* ✅ Logs complets avec structure uniforme (stdout, erreurs, API)
* ✅ Mise en place d’une mémoire locale (SQLite ou JSON)
* ✅ API auto-documentée avec Swagger, modèles Pydantic uniformes
* ✅ Docker opérationnel avec `.env` propre, secrets montés
* ✅ Interface minimaliste facultative (Streamlit, HTML/JS ou CLI)

---

## 📈 Étapes intermédiaires v2.x

### 🔹 `v2.1` — Structuration interne avancée

* Refactorisation complète des `/ping` avec décorateur `@safe_ping`
* Introduction de modèles Pydantic `PingResult`, `TokenInfo`, etc.
* Ajout du dossier `models/` central
* Nettoyage et réorganisation du `token_manager`
* Revue des tests pour coller aux nouveaux schémas typés

### 🔹 `v2.2` — Automatisations locales

* Création des endpoints `/run/command` et `/run/script`
* Mise en place d’un répertoire `scripts/` surveillé et limité
* Sécurité des entrées (filtrage de commandes autorisées)
* Journalisation complète des exécutions (stdout, stderr, retour code)

### 🔹 `v2.3` — Mémoire & persistance

* Mise en place d’un backend `memory/` : SQLite via SQLModel ou JSON segmentés par service
* Stockage des réponses API récentes, erreurs fréquentes, statistiques
* Implémentation d’un cache pour services lourds (Notion, Calendar)

### 🔹 `v2.4` — Authentification locale

* Création des endpoints `/login`, `/me`
* Protection JWT sur les endpoints critiques (`/run`, `/update`, `/refresh`...)
* Configuration d’un token admin dans `.env`
* Ajout des dépendances dans Swagger (securitySchemes)

### 🔹 `v2.5` — Interface locale simple

* Mise en place d’un mini dashboard avec Streamlit ou Flask/HTMX
* Affichage des logs, des modules actifs, déclenchement manuel d’actions
* Export en mode standalone si besoin (sur mobile ou serveur)

---

## 🚀 Hanuman v3.0 – Critères de complétion

* [ ] API multi-service avec ping et action minimale disponible (read/write)
* [ ] `run/command` et `run/script` utilisables et sécurisés
* [ ] Authentification active par token JWT simple
* [ ] Logs unifiés (rotation, différenciation stdout/err)
* [ ] Swagger complet avec modèles typés Pydantic
* [ ] Dockerfile stable, secrets sécurisés, `.env` injectable
* [ ] Interface de consultation minimaliste fonctionnelle (CLI, Web ou scriptable)
* [ ] Code versionné, testé, prêt à s'étendre (v4.0 : assistant IA, surveillance, agents)

---

## 🧰 Outils & exigences maximales

| Outil           | Exigence technique                         | Usage dans Hanuman                    |
| --------------- | ------------------------------------------ | ------------------------------------- |
| **FastAPI**     | Modularité, Swagger, sécurité, dépendances | Architecture, routes, doc automatique |
| **httpx**       | Gestion erreurs, session, retry, timeout   | Appels API propres et centralisés     |
| **Pydantic**    | Typage fort, validation, modèles           | Structure de réponse, Swagger         |
| **dotenv**      | Multi-env, sécurité, `.env` partagé        | Chargement centralisé de variables    |
| **uvicorn**     | Reload, logs, process main/thread          | Serveur dev & production              |
| **pytest**      | Tests unitaire + CI                        | Vérification continue                 |
| **Docker**      | Conteneurisation pro, secrets isolés       | Déploiement local ou serveur distant  |
| **SQLite/JSON** | Persistance légère, queryable              | Cache API, mémoire Hanuman            |
| **Git**         | Branches propres, tags, historique clair   | Suivi de version (`v2.1`, `v2.2`...)  |

---

## 🧱 Prochaine étape : `v2.1`

* [ ] Créer `/models/` avec typage Pydantic
* [ ] Réécrire tous les `ping_*` avec `@safe_ping`
* [ ] Nettoyer `token_manager`, ajouter support refresh pour OAuth
* [ ] Compléter les tests + Swagger automatiquement
* [ ] Préparer tag `v2.1` sur GitHub avec changelog propre

📘 *Plan validé le 15 juin 2025 à 21h40 – Déploiement stratégique officiel de Hanuman v3.0 initié.*
 
 ---

 Premier Palier :

 # 📘 README — Hanuman : Typage, Qualité, CI & GitHub Actions

## 🤖 Objectif du fil

Stabiliser la version 2.x de **Hanuman**, avec :

* Typage strict et conforme (`mypy`)
* Linting (PEP8 via `flake8`, `black`)
* Automatisation GitHub Actions (CI sur push/pull)
* Tests complets à chaque commit (pytest)

## 📁 Organisation du projet

* `src/hanuman/` : code principal (api, services, core, utils)
* `tests/` : tous les tests FastAPI/Pytest unitaires
* `.github/workflows/test.yml` : GitHub Action de test CI
* `pyproject.toml` : config unique (Poetry, mypy, flake8...)

## 🛠️ Stack technique

| Outil              | Usage                             |
| ------------------ | --------------------------------- |
| **Poetry**         | Gestion d'env, deps, scripts      |
| **FastAPI**        | API REST modulaire                |
| **mypy**           | Analyse statique de type (strict) |
| **pytest**         | Tests unitaires                   |
| **httpx**          | Requêtes asynchrones propres      |
| **GitHub Actions** | CI/CD sur push et pull            |
| **Pydantic**       | Modèles typés pour réponses/API   |
| **black**          | Formatage automatique             |
| **flake8**         | Lint PEP8                         |

## ✅ Tests en place

Chaque service possède un `ping` + fichier de test correspondant :

* `test_chess_ping.py`
* `test_github_ping.py`
* `test_notion_ping.py`
* `test_openai_ping.py`
* `test_obsidian_ping.py`
* `test_wikipedia_ping.py`
* `test_status.py`
* `test_env_loaded.py`

## 📊 GitHub Actions

Fichier : `.github/workflows/test.yml`

* Déclenché sur `push` et `pull_request`
* Matrix : Python 3.12 sur `ubuntu-latest`
* Installe poetry, dépendances, lance `pytest`
* Intégration avec les actions : `actions/setup-python`, `snok/install-poetry`

## ✏️ Typage avec Mypy

* Activation via `poetry add --group dev mypy`
* Config dans `[tool.mypy]` du `pyproject.toml`
* Exigences strictes : pas de `Any`, fonctions typées
* Problèmes récurrents corrigés :

  * `Function is missing a return type annotation`
  * `Missing type parameters for generic type "dict"`
  * `Untyped decorator makes function untyped`

### Solutions typiques apportées

```python
from typing import Any, Dict

def load_token_json(file: Path) -> Dict[str, Any]:
    ...
```

```python
@app.get("/notion/ping")
def ping_notion() -> PingResult:
    ...
```

## ⚖️ Gestion de l’historique Git

* Convention de commit pro :

```bash
Feat(GitHub): initialize GitHub Action logic with automated pytest on push
Perf(ping): normalize and document pings by modifying services. Version testée.
```

* Usage de `git tag v2.1`, `v2.2`...
* Restauration locale :

```bash
git restore path/to/file.py
```

## ❓ Problèmes rencontrés

* Mypy = long à stabiliser
* Typer chaque `dict` → `Dict[str, Any]`
* Fichiers ignorés par black à cause de `max-line-length`

## 🏃️ Prochaine étape : v2.1

* Finaliser typage de tous les fichiers API/Services
* Réduire les erreurs `mypy` à 0
* Ajouter un tag Git `v2.1` stable avec tests et CI OK
* Commencer `/run/script`, `/run/command` (v2.2)

---

💡 *Tous les fichiers modifiés ont été révisés, testés avec `pytest` et intégrés à la CI GitHub. Typage à 90 % conforme. Projet stable.*

---

## 📦 Hanuman `v2.1` — PingResult & CI stable

### ✅ Typage & structure
- Ajout du modèle `PingResult` (`pydantic.BaseModel`) pour tous les endpoints `/ping`
- Remplacement des retours `dict` → `PingResult` dans tous les services
- Tous les champs optionnels (`error`, `detail`, etc.) typés avec `= None`
- Décorateur `@safe_ping(source)` typé, compatible `mypy strict`

### 🔧 Qualité & CI
- Tous les fichiers validés `mypy` en mode `strict`
- 8/8 tests fonctionnels (`pytest`)
- Réorganisation des imports (`hanuman.models.ping`)
- Aucune dépendance instable, projet prêt pour `v2.2`

### 🚀 Prochaine étape : `v2.2`
- Endpoints `/run/command` et `/run/script`
- Authentification JWT simple
- Dashboard local ou CLI manuelle

