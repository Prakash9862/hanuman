# Hanuman

**Hanuman** est un système d'orchestration automatisé et modulaire conçu pour interagir avec des services web (API tierces) et des composants locaux (scripts, fichiers, commandes système) au sein d’un environnement personnel hautement sécurisé. Développé en **Python 3.11+** avec **FastAPI**, il sert de point d'entrée centralisé pour piloter, synchroniser et superviser des actions réparties sur différents systèmes.

---

## Objectifs

- Fournir une **API REST locale** modulaire extensible à l'infini
- Exécuter des modules d’automatisation (Notion, Google, GitHub, Obsidian…)
- Assurer une **sécurité absolue** (cloisonnement, non-exposition publique, tokens, logs)
- Garantir une **interopérabilité multi-systèmes** (Linux, Android, etc.)
- Préparer une montée en puissance vers des architectures complexes (event-driven, microservices)

---

## Spécifications techniques

### Framework :  
- **FastAPI** — Serveur ASGI rapide, typé, auto-documenté  
- ASGI Server : `uvicorn[standard]`

### Langage :  
- Python >= 3.11

### Sécurité :
- Authentification par JWT ou tokens statiques avec expiration
- Secrets stockés en `.env` ou fichiers chiffrés dans `secrets/`
- Pare-feu système (IPTables / UFW) restreignant l'accès à localhost ou VPN
- Aucun port exposé publiquement

### Modularité :
- Chaque action = 1 module Python indépendant, enregistré via routeur central
- Possibilité de charger dynamiquement des modules sans toucher au core

### Logging :
- Journalisation centralisée (`logs/hanuman.log`)
- Format JSON ou enrichi (timestamp, niveau, module, résultat)

### Tests :
- `pytest`, tests unitaires et fonctionnels pour chaque endpoint
- CI locale via `pre-commit`, lint (`flake8`, `black`, `isort`), typage `mypy`

---

## Arborescence du projet

# Arborescence professionnelle du projet Hanuman (FastAPI, 2025)

hanuman/
├── src/
│   └── hanuman/                       # Package principal Python
│       ├── main.py                   # Point d’entrée FastAPI
│       ├── api/                      # 🌐 Routes FastAPI (regroupées par domaine)
│       │   ├── __init__.py
│       │   └── status.py
│       ├── core/                     # 🔧 Infrastructure : config, logger, sécurité
│       │   ├── __init__.py
│       │   ├── config.py
│       │   ├── logging.py
│       │   └── security.py
│       ├── services/                 # ⚙️ Logique applicative (appel API Notion, GitHub…)
│       │   ├── __init__.py
│       │   └── notion_service.py
│       ├── models/                   # 📦 Schémas Pydantic (entrées / sorties / DTO)
│       │   ├── __init__.py
│       │   └── status.py
│       └── utils/                    # 🧩 Fonctions utilitaires
│           └── helpers.py
├── tests/                            # 🧪 Tests unitaires & d’intégration
│   ├── __init__.py
│   └── test_status.py
├── config/                           # ⚙️ Fichiers de configuration YAML ou JSON
│   ├── logging.yaml
│   └── hanuman_config.json
├── secrets/                          # 🔒 Clés, tokens, .env (non versionnés)
│   └── .gitkeep
├── logs/                             # 📝 Logs runtime
│   └── hanuman.log
├── data/                             # 🗂️ Fichiers de données temporaires ou traités
│   └── .gitkeep
├── .gitignore
├── README.md
├── pyproject.toml
└── poetry.lock

---

# 📘 Hanuman - README Général

## 🧭 Présentation

**Hanuman** est une API personnelle d'orchestration modulaire, développée en **Python 3.12** avec **FastAPI**, conçue pour centraliser et automatiser les intégrations entre services externes (GitHub, Notion, etc.) et composants locaux (scripts, fichiers, vault Obsidian…).

Ce projet est à la fois un **laboratoire d’apprentissage**, un **noyau personnel d’automatisation** et une **base de supervision logicielle**. Il repose sur des standards professionnels, tout en restant compact, testable et extensible.

---

## 🧱 Structure technique

```
hanuman/
├── .env                        # Clés privées, tokens d’API
├── config/
│   ├── logging.yaml           # Configuration des logs
│   └── hanuman_config.json    # (facultatif)
├── logs/
│   ├── hanuman.log            # Logs globaux DEBUG+
│   └── hanuman_error.log      # Logs d’erreur JSON
├── src/hanuman/
│   ├── main.py                # Entrée FastAPI
│   ├── api/                   # Routes (status, notion, github…)
│   ├── core/                  # Logging, config, sécurité
│   ├── services/              # Logique applicative
│   ├── models/                # Schémas Pydantic (optionnel)
│   └── utils/                 # Fonctions utilitaires
├── tests/                     # Tests Pytest par module
├── Makefile                   # Commandes raccourcies
├── pyproject.toml             # Dépendances (poetry, black…)
└── README.md                  # (ce fichier)
```

---

## 🎯 Objectifs principaux

* ⚙️ **Centraliser les intégrations** locales et API tierces
* 🧩 **Modularité** : chaque service = module indépendant
* 🔐 **Sécurité** : aucune exposition publique, tokens cloisonnés
* 🧪 **Testabilité** intégrée (pytest + convention "ok/error")
* 📓 **Logs** professionnels centralisés (DEBUG + ERROR JSON)
* 📡 **Évolutivité** : gestion propre pour ajout de services futurs

---

## ✅ Services actuellement intégrés

| Service   | Route            | Token `.env` | Testé | Dossier            | Service Python                 |
| --------- | ---------------- | ------------ | ----- | ------------------ | ------------------------------ |
| Status    | `/status`        | ❌            | ✅     | `api/status.py`    | — intégré                      |
| Notion    | `/notion/ping`   | ✅            | ✅     | `api/notion.py`    | `services/notion_service.py`   |
| GitHub    | `/github/ping`   | ✅            | ✅     | `api/github.py`    | `services/github_service.py`   |
| Chess.com | `/chess/ping`    | ❌            | ✅     | `api/chess_com.py` | `services/chess_service.py`    |
| Obsidian  | `/obsidian/ping` | ❌            | ✅     | `api/obsidian.py`  | `services/obsidian_service.py` |

---

## 🔧 Développement & Tests

### 🛠️ Makefile

```make
make run      # Lance uvicorn avec reload
make test     # Lance pytest
make format   # Formate avec black
make lint     # Lint avec flake8
make clean    # Supprime les caches Python
```

### 🧪 Convention de test

* Tous les pings retournent un `"ok": true/false`
* Si erreur : champ `"error"` obligatoire
* Tous les tests sont dans `tests/` avec un `test_*_ping.py` par service

---

## 🔒 Variables d’environnement (`.env`)

| Variable       | Utilisé par         | Usage                   |
| -------------- | ------------------- | ----------------------- |
| `NOTION_TOKEN` | `notion_service.py` | Appel API Notion        |
| `GITHUB_TOKEN` | `github_service.py` | Authentification GitHub |

---

## 🪵 Logging

Configuration : `config/logging.yaml`

* 📘 `logs/hanuman.log` : tous les logs DEBUG+, INFO, etc.
* ❗ `logs/hanuman_error.log` : logs d’erreurs au format JSON
* Préfixes systématiques : `[hanuman.api.nom]`, `[hanuman.services.nom]`

---

## 📓 Notes internes

* Obsidian Vault utilisé : `/home/prakash/Prakash/obsidian/Privé`
* Chaque route est testable isolément (API REST pure)
* Aucun service n'est couplé aux autres (architecture propre)
* Tous les modules sont prévus pour être débrayables individuellement
* Projet en constante évolution, structuré pour rester robuste dans la durée

---

## 📌 État du système

* Pings fonctionnels : ✅ 5/5
* Tests validés : ✅ 5/5
* Logging opérationnel : ✅ 100 %
* `.env` actif : ✅ 2 clés principales (Notion, GitHub)
* Uvicorn + FastAPI tournent localement : ✅ stable
* Prochaine étape : intégrer des **automations réelles** par service

---

## 🔜 À faire

* 🔄 Ajout de fonctions avancées (push/pull Notion, GitHub issues…)
* 🔐 Intégration auth (JWT statique ou time-based)
* 🧠 Ajout de mémoire interne (SQLite / JSON local ?)
* 🧪 Déploiement Dockerisé (local uniquement)

📘 *Version actuelle : Hanuman v1 — Phase d’intégration terminée*

> “The monkey-god who saute par-dessus les architectures – voilà Hanuman.”
