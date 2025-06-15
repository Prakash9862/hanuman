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
