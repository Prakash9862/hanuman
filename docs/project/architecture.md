# Architecture

## Vue d’ensemble

Hanuman est un monolithe modulaire local. Le frontend, la TUI et les clients
HTTP utilisent le même backend FastAPI. Le backend appelle des services web,
des fichiers locaux et des programmes installés sur le poste.

```text
┌──────────────── Interfaces ────────────────┐
│ React/Vite        FastAPI docs        TUI  │
└──────────────────────┬─────────────────────┘
                       v
┌──────────────── API / routes ──────────────┐
│ validation HTTP, sérialisation, délégation │
└──────────────┬─────────────────┬───────────┘
               v                 v
      ┌─ Orchestrations ─┐  ┌─ Services ────┐
      │ intention, ordre │  │ capacités     │
      │ transformation   │  │ réutilisables │
      └─────────┬────────┘  └──────┬────────┘
                └──────────┬───────┘
                           v
             ┌──── Connecteurs réels ────┐
             │ HTTP, OAuth, fichiers, CLI │
             └─────────────┬──────────────┘
                           v
        APIs externes, vault Obsidian, Stockfish
```

## Point d’entrée

Le point d’entrée canonique est `hanuman.main:app`. Il assemble l’application
complète et est utilisé par le Makefile et l’image Docker.

`hanuman.api.core.main:app` construit encore une application minimale ne
contenant que les routes d’orchestration. C’est une surface historique, pas le
point d’entrée recommandé.

Au 27 juillet 2026, l’import de l’application canonique expose 52 opérations.
La référence durable est toutefois OpenAPI :

```bash
poetry run uvicorn hanuman.main:app --host 127.0.0.1 --port 8000
```

Puis consulter `/docs` ou `/openapi.json`.

## Frontend

`frontend/` contient une SPA React 19 construite avec Vite. Elle fournit des
espaces pour :

- la constellation et le catalogue des orchestrations ;
- Gmail et Calendar ;
- Obsidian/Notion et Wikipédia/Notion ;
- Chess/Obsidian ;
- les ressources ;
- la santé du système.

Le frontend ne contient pas la logique métier. Il appelle l’API via le proxy
Vite ou des URL locales. Certains statuts restent des représentations
d’interface et ne prouvent pas à eux seuls la santé d’un connecteur.

## API

Deux familles historiques coexistent :

| Dossier | Rôle actuel |
|---|---|
| `api/core/` | routes par plateforme, diagnostics et application minimale historique |
| `api/routers/` | flux, catalogues, Gmail, Resources, Chess et dashboard |

Les routes doivent valider HTTP, appeler une capacité et sérialiser le résultat.
Elles ne devraient pas connaître les détails d’une API tierce.

## Services

Les services ont deux formes :

- `services/core/` : services centrés sur une plateforme ;
- `services/*.py` : capacités transverses, surtout le domaine Chess.

Ils portent l’interface Python réutilisable, les validations métier locales et
une partie des accès externes. Les services Chess isolent notamment l’analyse,
les chemins sûrs, les écritures atomiques, l’agrégation et les vues.

## Connecteurs

Le registre `services/connectors_registry.py` décrit les connecteurs visibles et
leurs capacités. Il sert de catalogue, pas encore de contrat d’exécution
commun.

La couche `services/adapters/` contient de minces clients GitHub et Notion,
mais elle n’est pas la frontière universelle décrite par l’ancienne
documentation. Plusieurs services effectuent eux-mêmes leurs appels HTTP et
certaines orchestrations historiques utilisent directement `urllib`.

Architecture réelle :

```text
service ───────────────> API externe
service -> client fin ─> API externe
orchestration ─────────> API externe     # dette historique
```

Le principe cible reste : une orchestration ne parle pas directement à une API
externe.

## Orchestrations

`src/hanuman/orchestrations/` contient des modules appelables depuis l’API, une
CLI ou des services. Leur maturité est hétérogène :

- Chess.com → Stockfish → Obsidian est le flux le plus développé ;
- Obsidian → Notion et Wikipédia → Notion sont disponibles ;
- GitHub → Notion dispose d’une orchestration et d’un journal de run ;
- Wikipédia + OpenAI et certaines synthèses Chess restent des capacités sans
  interface principale.

Les orchestrations actuelles sont des fonctions Python, pas un moteur de graphe
ou un ordonnanceur générique.

## Ressources

Le terme « ressource » désigne un objet découvert ou manipulé. Le module
`resources_service.py` normalise des recherches YouTube, Gallica et IMSLP, et
construit des liens Maps. Il ne constitue ni une base centrale ni une
bibliothèque persistante.

Stockfish et les programmes locaux apparaissent dans l’espace Resources pour
des raisons opératoires, mais ce sont des capacités locales plutôt que des
ressources distantes.

## Modèles

`models/` contient les contrats Pydantic et dataclasses utilisés par les
connecteurs, l’API et Chess. Il n’existe pas encore de modèle universel de
ressource ou de résultat d’orchestration.

## Persistance

Hanuman n’utilise pas de base de données centrale.

| Donnée | Persistance |
|---|---|
| secrets généraux | variables d’environnement et fichiers locaux ignorés |
| jetons OAuth | fichiers locaux propres à Gmail et Calendar |
| notes et analyses Chess | vault Obsidian externe |
| état de queue Stockfish | fichier JSON atomique dans la racine Chess |
| logs | fichiers JSON rotatifs et journal JSONL |
| état de santé UI | `localStorage` |

Les systèmes externes restent sources de vérité selon le flux. Hanuman conserve
les dérivés nécessaires, notamment pour Chess.

## Dépendances autorisées

```text
interface -> API -> orchestration -> service -> connecteur
                       |              |
                       └-> modèle <----┘
```

Règles :

- une route ne construit pas un workflow inter-outils ;
- un service de plateforme n’appelle pas un autre service de plateforme pour
  former un flux ;
- une orchestration dépend d’interfaces de capacité, pas de FastAPI ;
- un connecteur ne dépend ni du frontend ni des routes ;
- les effets fichiers et réseau restent explicites et testables.

Les écarts existants sont documentés dans
[l’état actuel](current-state.md), pas transformés en principes.
