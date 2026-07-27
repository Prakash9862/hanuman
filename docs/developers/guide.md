# Guide développeur

## Organisation du dépôt

```text
frontend/                 SPA React/Vite
src/hanuman/
  api/                    routes FastAPI
  config/                 configuration Chess et environnement
  core/                   infrastructure transversale
  models/                 contrats de données
  orchestrations/         intentions exécutables
  services/               capacités et logique réutilisable
  tui/                    interface Textual
  utils/                  utilitaires génériques
tests/                    tests Python
docs/                     documentation de référence et archives
```

## Placer une modification

| Besoin | Emplacement |
|---|---|
| valider une requête HTTP | `api/` |
| coordonner plusieurs capacités | `orchestrations/` |
| exposer une opération Python réutilisable | `services/` |
| parler à un fournisseur ou au système | connecteur/service frontière |
| définir un contrat échangé | `models/` |
| rendre une interaction | `frontend/` ou `tui/` |

La question principale est : « qui doit connaître cette décision ? » Une route
ne doit pas connaître une politique de synchronisation ; un client HTTP ne doit
pas connaître un workflow.

## Style Python

- Python 3.12 minimum.
- Typage strict mypy.
- Black pour le formatage, Ruff pour le lint et les imports.
- Fonctions et classes nommées par intention.
- Effets réseau, fichiers et processus visibles dans l’API du composant.
- Pas de secret, chemin personnel ou état global implicite.
- Une exception doit porter un contexte exploitable sans exposer de secret.

Le projet configure Black à 100 caractères et Ruff à 88 avec `E501` ignoré.
Ne tentez pas d’aligner ces valeurs dans une modification sans rapport.

## Style TypeScript/React

- TypeScript strict selon les `tsconfig`.
- Composants fonctionnels et état local explicite.
- Les statuts affichés proviennent du backend quand ils décrivent une capacité
  réelle.
- Les appels API passent par une base locale configurable ou le proxy Vite.
- Une page de connecteur ne doit pas devenir l’unité produit par défaut :
  préférer une intention inter-outils.

## Tests

Les tests doivent :

- être déterministes et sans secret réel ;
- simuler réseau, OAuth, horloge et processus externes ;
- couvrir les erreurs et les effets, pas seulement le chemin heureux ;
- utiliser `tmp_path` pour les fichiers ;
- vérifier l’idempotence et la préservation des données pour toute écriture.

Voir [Tests](testing.md).

## Coverage

Le Makefile demande actuellement 90 % au rapport global. La documentation ne
garantit pas que ce seuil est atteint, et la suite complète peut bloquer dans
l’environnement local. Une contribution ne doit ni abaisser le seuil ni
gonfler artificiellement la mesure.

Mesurer la source séparément lorsque le diagnostic l’exige :

```bash
poetry run coverage run --source=src/hanuman -m pytest -q
poetry run coverage report -m
```

## Git

- Créer des commits atomiques décrivant l’intention.
- Ne pas mélanger refactoring, comportement et documentation sans nécessité.
- Examiner `git diff` et `git status` avant chaque commit.
- Ne pas versionner `.env`, tokens, logs, vaults ou rapports générés.
- Utiliser des messages de type `docs:`, `feat:`, `fix:`, `test:` ou `refactor:`.

Une branche doit rester relisible commit par commit. Ne réécrivez pas
l’historique partagé sans accord.

## Revue de code

La revue vérifie :

1. la couche choisie et les dépendances ;
2. les effets et permissions ;
3. les sources de vérité et l’identité ;
4. les erreurs partielles et l’idempotence ;
5. les tests et la preuve de vérification ;
6. la cohérence de la documentation ;
7. l’absence de données personnelles ou secrets.

Pour un nouveau flux, joindre son contrat documentaire. Pour une décision
structurante, proposer un ADR.

## Documentation

- Le code disponible est documenté au présent.
- Une idée est marquée « envisagée » ou placée dans la roadmap.
- Une spécification n’est pas une preuve d’implémentation.
- Les détails d’API copiés à la main sont évités au profit d’OpenAPI.
- Les rapports ponctuels sont archivés dans `docs/history/`.
- Tout lien modifié doit être vérifié.

## Bonnes pratiques

- Commencer par un cas réel avant une abstraction générique.
- Préférer un petit service testable à une couche universelle spéculative.
- Garder les outils externes propriétaires de leurs objets spécialisés.
- Appliquer le moindre privilège.
- Rendre les écritures atomiques ou explicitement partielles.
- Montrer « inconnu » plutôt qu’un faux état sain.
