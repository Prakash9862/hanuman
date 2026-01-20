# Cerveau GitHub local — synchronisation + état système

Ce document propose une solution simple pour remettre tous vos projets GitHub
sur votre PC et créer un "cerveau" local qui vous donne accès aux détails de vos
dépôts tout en vérifiant l’état de votre système.

## Objectif

- **Synchroniser** automatiquement tous vos dépôts GitHub en local.
- **Indexer** vos dépôts pour retrouver rapidement leurs informations.
- **Vérifier** l’état de votre machine (disque, mémoire, uptime).

## Prérequis

- GitHub CLI `gh` (authentifiée avec votre compte).
- `git`
- `jq`

Exemple d’installation (Linux) :

```bash
sudo apt-get update
sudo apt-get install -y git jq
```

Pour `gh`, suivez la doc officielle : https://cli.github.com/

## Script "cerveau"

Le script suivant :

1. Liste vos dépôts GitHub via `gh`.
2. Clone ou met à jour chaque dépôt.
3. Stocke un index JSON local.
4. Écrit un résumé de l’état du système.

Le script est dans `scripts/github_brain.sh`.

### Utilisation

```bash
chmod +x scripts/github_brain.sh
./scripts/github_brain.sh
```

### Variables utiles

```bash
BASE_DIR=~/GitHub \
BRAIN_DIR=~/.github_brain \
LIMIT=1000 \
./scripts/github_brain.sh
```

Pour limiter à une organisation précise :

```bash
ORG=mon-organisation ./scripts/github_brain.sh
```

## Résultat attendu

- Tous vos dépôts sont synchronisés dans `~/GitHub/<owner>/<repo>`.
- Un index des dépôts est généré dans `~/.github_brain/repos.json`.
- Un état du système est généré dans `~/.github_brain/system_status.txt`.

## Idées d’amélioration

- Ajouter un index Markdown ou HTML pour parcourir vos projets.
- Ajouter une recherche plein texte sur les READMEs.
- Envoyer une alerte si l’espace disque est faible.
