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
