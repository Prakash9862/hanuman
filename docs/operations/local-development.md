# Exploitation locale

## Installation

Prérequis :

- Python 3.12 ou 3.13 ;
- Poetry ;
- Node.js et npm ;
- les programmes locaux propres aux flux utilisés, par exemple Stockfish.

```bash
poetry install
npm --prefix frontend install
```

## Lancement complet

```bash
make run
```

Cette commande lance :

- `hanuman.main:app` sur `127.0.0.1:8000` ;
- Vite sur `127.0.0.1:5173` ;
- le navigateur local si disponible.

Les PID et sorties sont placés dans des fichiers `.hanuman-*` à la racine.

```bash
make stop
make restart
```

## API seule

```bash
poetry run uvicorn hanuman.main:app \
  --host 127.0.0.1 \
  --port 8000
```

## Frontend seul

```bash
npm --prefix frontend run dev -- --host 127.0.0.1
```

Le proxy Vite redirige `/api` vers l’API locale.

## Docker

Le dépôt possède un Dockerfile multi-stage et un `docker-compose.yml`.

```bash
docker compose build
docker compose up
```

Attention : le conteneur écoute sur `0.0.0.0` et Compose publie le port 8000.
Cela ne transforme pas Hanuman en service sûr pour le LAN ou Internet. Contrôler
le pare-feu et l’interface publiée, ou préférer le lancement natif sur
loopback.

Les anciens documents Docker décrivaient des workflows et outils qui ont
évolué. Les fichiers Docker suivis sont la référence.

## Logs

La configuration `structlog` écrit en console et dans `logs/`. Les fichiers
sont rotatifs et peuvent contenir des chemins ou métadonnées sensibles.

Pour un diagnostic :

1. reproduire avec le niveau minimal nécessaire ;
2. relever le `request_id` quand il existe ;
3. expurger secrets et données personnelles avant partage ;
4. ne pas committer les journaux.

## Arrêt et reprise

Les orchestrations n’ont pas toutes un état persistant commun. La queue
Stockfish possède son propre cycle de vie ; les autres flux peuvent n’offrir
qu’un résultat synchrone ou un processus lancé par le dashboard.

Avant de relancer une écriture après interruption, vérifier l’objet cible et les
doublons. Ne supposez pas l’idempotence si elle n’est pas documentée pour le
flux.
