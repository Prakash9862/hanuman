# API

## Référence canonique

L’application publique est :

```text
hanuman.main:app
```

Lancer l’API :

```bash
poetry run uvicorn hanuman.main:app --host 127.0.0.1 --port 8000
```

Les contrats exacts sont générés depuis le code :

- Swagger : `http://127.0.0.1:8000/docs`
- ReDoc : `http://127.0.0.1:8000/redoc`
- OpenAPI : `http://127.0.0.1:8000/openapi.json`

Cette page décrit les familles de routes sans recopier un schéma qui deviendrait
rapidement obsolète.

## Familles

| Préfixe | Rôle | Effets possibles |
|---|---|---|
| `/status`, `/log` | diagnostic local | lecture |
| `/connectors` | catalogue de capacités | lecture |
| `/gmail` | OAuth et messages Gmail | token local, lecture distante |
| `/calendar` | OAuth, calendriers, événements | token local, lecture distante |
| `/resources` | recherches et opérateur Stockfish | réseau, processus et fichiers selon la route |
| `/orchestrations` | exploration et publication | lecture locale/distante, écriture Notion |
| `/chess` | synchronisation Chess.com | réseau et écriture Obsidian |
| `/dashboard` | résumé et lancement historique | lecture et processus |
| routes de plateforme | pings et opérations simples | dépend du connecteur |

## Règles d’utilisation

- Ne pas exposer cette API hors loopback sans nouvelle revue de sécurité.
- Consulter OpenAPI avant d’intégrer un client : les formats ne sont pas encore
  versionnés sous `/api/v1`.
- Un HTTP 200 historique peut encapsuler un état métier négatif sur certaines
  routes ; vérifier le corps.
- Les routes d’écriture ne partagent pas encore toutes une preview ou un
  `run_id`.

## Application historique

`hanuman.api.core.main:app` ne contient qu’un sous-ensemble de routes. Elle
subsiste pour compatibilité interne mais ne doit pas être utilisée pour lancer
Hanuman.
