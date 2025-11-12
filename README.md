# 🐒 Hanuman — API, Services et Orchestrations

> **Version : v5.1-green — Build stable et typée (Python 3.12, FastAPI, Poetry)**
> "Celui qui relie les mondes." — Hanuman, gardien du pont entre GitHub, Notion et Obsidian

---

## 🌍 Vision générale

**Hanuman** est une API d’orchestration écrite en Python (FastAPI) destinée à centraliser, automatiser et relier différents services externes :

- Notion (bases de données, synchronisation de contenu)
- Obsidian (vaults locaux, markdowns synchronisés)
- GitHub (issues, repos, commits)
- Wikipedia (requêtes contextuelles)
- OpenAI (génération de texte, analyse de données)
- Calendar (Google Calendar, gestion des événements)
- Chess.com (données d’échecs et statistiques)

L’objectif est de permettre une **automatisation intelligente**, où Hanuman agit comme un **cerveau intermédiaire** : il observe, collecte, synchronise et structure les données pour les rendre interopérables entre les plateformes.

---

## ⚙️ Architecture du projet

Hanuman repose sur une architecture modulaire, inspirée des bonnes pratiques FastAPI :

```
src/
├── hanuman/
│   ├── api/                # Couches d'exposition (FastAPI)
│   │   ├── core/           # Routes principales et pings
│   │   └── orchestrations_router.py
│   ├── core/               # Configuration et middleware
│   ├── services/           # Couches logiques et d'intégration
│   │   ├── core/           # Services individuels (Notion, GitHub...)
│   │   └── orchestrations/ # Logique d'orchestration inter-services
│   ├── models/             # Schémas de données Pydantic
│   ├── utils/              # Aides génériques, décorateurs, helpers
│   └── main.py             # Point d'entrée FastAPI (app)
```

### 🧩 Séparation des responsabilités

| Couche             | Description                                                          |
| ------------------ | -------------------------------------------------------------------- |
| **API**            | Routes FastAPI exposées publiquement (HTTP endpoints)                |
| **Core**           | Gestion interne (config, sécurité, logs, middleware)                 |
| **Services**       | Modules métier spécifiques à chaque intégration (Notion, GitHub...)  |
| **Orchestrations** | Fonctions combinant plusieurs services pour créer des flux complexes |
| **Models**         | Objets structurés (Pydantic) garantissant la cohérence des échanges  |
| **Utils**          | Fonctions utilitaires transversales, non couplées à un service       |

---

## 🧠 Fonctionnement global

Hanuman agit comme une **passerelle centralisée** :

1. Chaque service (`services/core/*.py`) contient une logique d’appel API dédiée.
2. Les orchestrations combinent plusieurs de ces services pour accomplir des tâches concrètes (ex : créer une page Notion à partir d’un repo GitHub).
3. L’application expose ces fonctions via des endpoints HTTP, utilisables en local, sur serveur ou intégrées à d’autres outils (Notion, scripts Ankura, Cerveau général, etc.).

### Exemple de flux

```
[GitHub] → Issues récupérées → [Hanuman] → Transformation → [Notion] → Page créée
```

Ce pipeline est piloté via une orchestration `sync_github_to_notion()` située dans `services/orchestrations/github_sync_notion_services.py`.

---

## 🧬 Technologies principales

| Composant       | Rôle                                         |
| --------------- | -------------------------------------------- |
| **Python 3.12** | Langage principal                            |
| **FastAPI**     | Framework web asynchrone                     |
| **Poetry**      | Gestionnaire de dépendances                  |
| **Uvicorn**     | Serveur ASGI de déploiement local            |
| **Ruff**        | Linter + formateur ultra-rapide              |
| **mypy**        | Vérification statique des types              |
| **pytest**      | Tests unitaires et fonctionnels              |
| **dotenv**      | Gestion des variables d’environnement (.env) |
| **Pydantic**    | Validation stricte des modèles               |

---

## 🧾 Configuration typage et qualité

### **mypy.ini** (stable et silencieuse)

```ini
[mypy]
python_version = 3.12
strict = False
ignore_missing_imports = True
warn_unused_ignores = True
warn_return_any = True
disable_error_code = no-untyped-def,misc,type-arg

[mypy-tests.*]
ignore_errors = True
```

### **Makefile** (raccourcis universels)

```makefile
# Formatage et lint
dev: fmt lint

fmt: ## Formate le code
	poetry run ruff format .

lint: ## Corrige les erreurs mineures
	poetry run ruff check . --fix

# Typage
typecheck: ## Vérifie les types
	poetry run mypy src/hanuman tests

# Tests
test: ## Lance Pytest
	poetry run pytest -q

# Vérification globale
check: fmt lint typecheck test

# Lancement API
run:
	PYTHONPATH=src poetry run uvicorn hanuman.main:app --reload --host 127.0.0.1 --port 8000
```

---

## 🔍 Validation finale

| Étape           | Outil    | Statut                    |
| --------------- | -------- | ------------------------- |
| Formatage       | Ruff     | ✅ OK (60 fichiers)       |
| Lint            | Ruff fix | ✅ OK                     |
| Typage          | mypy     | ✅ 0 erreur               |
| Tests unitaires | pytest   | ✅ 10/10 passed           |
| Serveur local   | Uvicorn  | ✅ 127.0.0.1:8000/docs    |
| Swagger         | FastAPI  | ✅ Toutes routes `200 OK` |

---

## 🧠 Orchestrations principales

| Orchestration                | Description                                                  | Statut           |
| ---------------------------- | ------------------------------------------------------------ | ---------------- |
| **sync_github_to_notion**    | Crée une page Notion à partir d’un repo GitHub (stub actuel) | ✅ Stable (mock) |
| **sync_obsidian_to_notion**  | Synchronisation bidirectionnelle des notes locales           | 🔜 En conception |
| **sync_calendar_to_notion**  | Export automatique des événements Google Calendar            | 🔜 Prévu         |
| **sync_wikipedia_to_notion** | Extraction automatique d’articles pour documentation         | 🔜 À implémenter |

---

## 🧩 Routes disponibles

### Core

```
GET /status/ping
GET /log/trace
```

### Services

```
GET /notion/ping
GET /openai/ping
GET /github/ping
GET /wikipedia/ping
GET /calendar/ping
GET /chess/ping
```

### Orchestrations

```
POST /orchestrations/ping
```

---

## 🔒 Gestion des environnements

Le fichier `.env` doit contenir les clés nécessaires :

```
NOTION_TOKEN=secret_...
GITHUB_TOKEN=ghp_...
OPENAI_API_KEY=sk-...
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
NOTION_PARENT_ID=...
```

Chargement automatique :

```python
from dotenv import load_dotenv
load_dotenv(dotenv_path=".env", override=True)
```

---

## 🧱 Déploiement local

```bash
git clone https://github.com/Prakash/hanuman.git
cd hanuman
poetry install
make check
make run
```

Accessible à : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

---

## 🧩 Philosophie du projet

Hanuman est conçu comme **le médiateur des données** : il relie, harmonise et automatise.
Il s’inscrit dans un écosystème plus vaste comprenant :

- 🧱 **Ankura** : moteur de scripts et d’extraction (back-end technique)
- 🧭 **Cerveau Général** : interface CLI/desktop de pilotage
- 🗃️ **Notion** : base de données de référence
- 🗺️ **Obsidian** : mémoire documentaire et graphes

Chaque service Hanuman correspond à un “nerf”, chaque orchestration à un “réflexe”.

> Hanuman n’est pas une simple API : c’est un **système nerveux numérique**.

---

## 🧩 Roadmap 2026

| Priorité | Module                    | Objectif                                                   |
| -------- | ------------------------- | ---------------------------------------------------------- |
| 🚀       | `sync_obsidian_to_notion` | Synchronisation complète markdown ↔ Notion                 |
| 🧠       | `github_issues_to_notion` | Intégration avancée des issues GitHub                      |
| 📅       | `calendar_sync`           | Gestion bidirectionnelle des événements Google             |
| 📚       | `docs_generator`          | Génération automatique de documentation à partir des bases |
| 💬       | `chat_agent`              | Endpoint conversationnel (liaison avec Cerveau Général)    |

---

## 🏁 État du système — Novembre 2025

| Composant    | Version | État           |
| ------------ | ------- | -------------- |
| API FastAPI  | 5.1     | ✅ Stable      |
| Makefile     | 3.0     | ✅ Cohérent    |
| Typage mypy  | Full    | ✅ Aucun bruit |
| Tests pytest | 10/10   | ✅ Validé      |
| Swagger UI   | Actif   | ✅ 200 OK      |
| CI/CD GitHub | À venir | 🔜             |

---

## 📜 Licence

MIT © 2025 — Projet Hanuman
Créé par Vincent (Prakash) — avec Lyra 🩵

> “Entre l’esprit et la matière, Hanuman construit le pont.”
