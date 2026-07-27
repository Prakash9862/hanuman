# Hanuman

Hanuman est un hub d’orchestration personnel et local. Il relie des outils
spécialisés sans chercher à les remplacer.

```text
GitHub ─┐
Notion ─┤
Gmail  ─┼──> Hanuman ──> flux contrôlés, transformations et résultats
Chess  ─┤
Obsidian┘
```

GitHub reste l’endroit du code. Notion reste un espace structuré. Obsidian reste
un ensemble de notes Markdown locales. Google Calendar reste le calendrier.
Hanuman coordonne leurs échanges.

## Pourquoi Hanuman existe

Une même intention traverse souvent plusieurs applications : publier une note,
transformer une source en page structurée, analyser des parties d’échecs ou
rapprocher des objets stockés ailleurs. Sans orchestration, l’utilisateur doit
recopier les données, réconcilier les formats et se souvenir des effets produits.

Hanuman centralise cette logique de coordination :

- il expose des capacités externes et locales sous une interface commune ;
- il compose ces capacités dans des orchestrations réutilisables ;
- il transforme les données sans devenir leur propriétaire universel ;
- il conserve la provenance et les résultats techniques nécessaires ;
- il laisse chaque outil spécialisé remplir son rôle.

Hanuman n’est ni un clone de Notion ou d’Obsidian, ni un agrégateur qui aspire
toutes les données, ni un agent autonome général.

## Ce qui fonctionne aujourd’hui

Le dépôt contient :

- une API FastAPI locale ;
- une interface React/Vite et une TUI Textual ;
- des connecteurs web et locaux ;
- des flux de publication vers Notion ;
- un domaine Chess avancé reliant Chess.com, Stockfish et Obsidian ;
- des capacités de lecture Gmail et Google Calendar ;
- un catalogue de ressources pour YouTube, Gallica, IMSLP et Google Maps.

Les niveaux de maturité et les limites sont détaillés dans
[l’état actuel](docs/project/current-state.md). La documentation ne présente pas
les idées de roadmap comme des fonctions disponibles.

## Démarrage rapide

Prérequis : Python 3.12 ou 3.13, Poetry et Node.js/npm.

```bash
poetry install
npm --prefix frontend install
make run
```

L’interface est ensuite disponible sur `http://127.0.0.1:5173` et Swagger sur
`http://127.0.0.1:8000/docs`.

`make run` lie les deux serveurs à l’interface loopback. Hanuman est conçu pour
un usage local et mono-utilisateur ; ne l’exposez pas sur un réseau sans revoir
son modèle de sécurité.

Les connecteurs nécessitent des variables ou fichiers d’authentification
distincts. Consultez [la configuration](docs/operations/configuration.md) avant
d’activer un flux.

## Développer

```bash
make format-check
make lint
make typecheck
make test
npm --prefix frontend run build
```

Dans l’environnement audité le 27 juillet 2026, la collecte trouve 492 tests,
mais la suite complète reste susceptible de se bloquer sur la pile
`TestClient`. Ce nombre est un relevé daté, pas un badge permanent. Voir
[le guide de tests](docs/developers/testing.md).

## Lire la documentation

Commencez par :

1. [Vision](docs/project/vision.md)
2. [Concepts](docs/project/concepts.md)
3. [Architecture](docs/project/architecture.md)
4. [État actuel](docs/project/current-state.md)
5. [Guide développeur](docs/developers/guide.md)

L’[index documentaire](docs/README.md) référence ensuite les connecteurs,
orchestrations, opérations, ADR, spécifications et archives.

## Licence

Hanuman est distribué sous licence MIT.
