# Tests

## Commandes

```bash
make test
make format-check
make lint
make typecheck
npm --prefix frontend run build
```

La couverture :

```bash
make coverage
```

Le Makefile applique `COVERAGE_MIN=90` par défaut. Ce seuil est une politique
de commande, pas une affirmation que l’état courant le satisfait.

## Organisation

Les tests reproduisent les zones principales :

```text
tests/
  api/
  cli/
  config/
  core/
  orchestrations/
  services/
  tui/
  utils/
```

Les appels externes sont simulés. Les tests d’écriture utilisent des
répertoires temporaires et doivent vérifier les fichiers préexistants.

## État connu au 27 juillet 2026

```bash
poetry run pytest --collect-only -q
```

collecte 492 tests.

```bash
poetry run pytest -q
```

reste sans sortie après plus d’une minute dans l’environnement audité et doit
être interrompu. Les rapports historiques ont déjà reproduit un blocage de la
pile FastAPI/Starlette `TestClient`, y compris sur des tests isolés.

Conséquences :

- ne pas annoncer que toute la suite passe sans exécution terminée ;
- diagnostiquer en CI propre avant d’attribuer le blocage au code Hanuman ;
- ne pas publier une couverture issue d’une sous-suite comme couverture totale.

## Diagnostic du blocage

```bash
poetry run pytest -vv -x
poetry run pytest path/to/test.py::test_name -vv
poetry show fastapi starlette httpx anyio
```

Utiliser une limite de temps externe si nécessaire. Consigner le premier test
bloqué, les versions et l’environnement. Ne mettez pas à jour des dépendances
dans un changement sans rapport.

## Critères par type

| Changement | Vérification minimale |
|---|---|
| transformation pure | tests unitaires et cas limites |
| route | appel direct du handler et test HTTP quand la pile fonctionne |
| connecteur | transport simulé, timeout, auth, pagination, erreurs |
| orchestration | sources, effets, idempotence, échec partiel |
| fichier | confinement, symlink, atomicité, contenu humain |
| frontend | build TypeScript ; tests UI à ajouter si une suite est introduite |

## Chiffres

Le README ne contient pas de badge statique de tests ou couverture. Si un
rapport ponctuel doit citer un nombre, il indique :

- la date ;
- le commit ;
- la commande ;
- le périmètre ;
- les exclusions ;
- le statut complet ou bloqué.
