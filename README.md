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

hanuman/
├── app/
│ ├── main.py # Point d’entrée FastAPI
│ ├── core/ # Moteur principal, sécurité, routeur global
│ │ ├── config.py # Paramètres de configuration (chargés dynamiquement)
│ │ ├── logging.py # Initialisation des logs
│ │ ├── auth.py # Authentification, validation de token
│ │ └── loader.py # Chargement dynamique des modules
│ ├── modules/ # Automatisations individuelles (1 fichier = 1 fonctionnalité)
│ │ ├── notion_to_gcal.py
│ │ └── github_to_notion.py
│ └── models/ # Pydantic schemas pour validation des entrées
├── tests/
│ ├── test_status.py
│ └── test_auth.py
├── secrets/ # Fichiers chiffrés ou .env (non commités)
│ └── .env
├── config/
│ ├── logging.yaml # Config avancée du logger Python
│ └── hanuman_config.json # Paramètres externes (paths, profils, etc.)
├── logs/
│ └── hanuman.log # Fichier de log général
├── .gitignore
├── pyproject.toml # Géré avec Poetry
├── requirements.txt # Généré automatiquement
└── README.md

