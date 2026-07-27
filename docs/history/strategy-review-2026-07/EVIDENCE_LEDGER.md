# Registre de preuves

> Archive non normative — revue stratégique de juillet 2026.

## Mode d’emploi

[FAIT] Ce document distingue ce qui est observé de ce qui est interprété.

[PROPOSITION] Toute revue future devrait citer un fait de ce registre ou ajouter une nouvelle preuve avant de formuler une conclusion.

## Dépôt et historique

| Classe | Observation | Preuve |
|---|---|---|
| [FAIT] | `main` et `origin/main` pointent sur `69250d3`. | `git branch --all`, `git log --decorate` |
| [FAIT] | La branche locale `feat/chess-analysis-v1` possède 29 commits non présents sur `main`. | `git log --left-right --cherry-pick main...feat/chess-analysis-v1` |
| [FAIT] | Le diff de cette branche avec son ancêtre commun touche 16 fichiers, avec 1 833 insertions et 222 suppressions. | `git diff --stat main...feat/chess-analysis-v1` |
| [FAIT] | Des fichiers Resources et Chess sont modifiés à la fois dans cette branche longue et dans l’historique récent de `main`. | noms du diff de branche et commits `69250d3` à `93b7338` |
| [INFÉRENCE] | L’intégration future de la branche Chess présente un risque élevé de conflit et d’arbitrage fonctionnel, même si Git pouvait fusionner textuellement. | évolution concurrente des mêmes responsabilités |

## Architecture exécutée

| Classe | Observation | Preuve |
|---|---|---|
| [FAIT] | Le tree `HEAD` contient 71 fichiers Python sous `src/hanuman`. | `git ls-tree` |
| [FAIT] | Le code déclare 48 décorateurs de routes FastAPI. | `git grep '@router\\.'` |
| [FAIT] | Le registre déclare 11 connecteurs. | `connectors_registry.py` |
| [FAIT] | Le dossier des orchestrations contient dix modules fonctionnels hors `__init__.py`. | `src/hanuman/orchestrations/` |
| [FAIT] | `hanuman.main` inclut quinze routeurs issus de `api/core` et `api/routers`. | `src/hanuman/main.py` |
| [FAIT] | Les dossiers `services/adapters/github` et `services/adapters/notion` contiennent des fichiers clients vides. | taille et contenu des fichiers |
| [INFÉRENCE] | La couche adapter documentée n’est pas une frontière exécutée aujourd’hui. | fichiers vides et appels HTTP situés dans services/orchestrations |

## Configuration et exploitation

| Classe | Observation | Preuve |
|---|---|---|
| [FAIT] | La configuration est lue via `pydantic-settings`, `config/env.py`, des accès directs à `os.environ` et deux appels à `load_dotenv`. | recherche dans `src/hanuman` |
| [FAIT] | `hanuman.main` appelle `load_dotenv(dotenv_path=".env", override=True)`. | `src/hanuman/main.py` |
| [FAIT] | Les deux applications FastAPI configurent CORS avec `allow_origins=["*"]` et `allow_credentials=True`. | `main.py`, `api/core/main.py` |
| [FAIT] | Le dashboard et la TUI lancent des processus avec `subprocess.Popen`. | `dashboard.py`, `tui/app.py` |
| [FAIT] | Le gestionnaire de tokens générique écrit dans `secrets/` sans appel explicite à `chmod`; Gmail applique `0600` à son token. | `token_manager.py`, `core/gmail.py` |
| [INFÉRENCE] | Les politiques de configuration, processus et secrets ne sont pas uniformes. | mécanismes distincts observés |

## Tests et qualité

| Classe | Observation | Preuve |
|---|---|---|
| [FAIT] | Le tree `HEAD` contient 41 fichiers de tests nommés `test*.py`. | `git ls-tree` |
| [FAIT] | Le README affirme à plusieurs endroits « 146 tests » et une couverture proche de 92 %. | `README.md` |
| [FAIT] | Le rapport de nuit présent dans le working tree consigne 160 tests collectés avant ajout local, puis 171, et une couverture partielle de 67 % puis 70 %. | `docs/CODEX_NIGHT_REPORT.md` |
| [FAIT] | Ce rapport précise que les appels `TestClient` se suspendent dans l’environnement local, y compris pour une application FastAPI minimale. | même rapport |
| [INFÉRENCE] | Les chiffres qualité du README ne sont pas une source fiable et reproductible en l’état. | contradiction entre assertions non datées et mesure documentée |
| [HYPOTHÈSE] | Le blocage `TestClient` pourrait provenir d’une interaction de versions ou de l’environnement plutôt que du code Hanuman. | reproduction minimale rapportée; cause non démontrée |

## Documentation et vision

| Classe | Observation | Preuve |
|---|---|---|
| [FAIT] | Le README dépasse 8 000 lignes et contient manifeste, guide, audit, roadmap, ADR et référence API. | titres et longueur de `README.md` |
| [FAIT] | Le README présente plugins, mémoire persistante et base de connaissances comme évolutions. | sections roadmap et perspectives |
| [FAIT] | La constitution stratégique adoptée sur la branche précédente rejette la base de connaissances universelle et conditionne plugins et agents. | `docs/strategy/HANUMAN.md`, `FEATURE_PIPELINE.md` |
| [INFÉRENCE] | Deux visions coexistent : centraliser la connaissance et coordonner des systèmes de référence externes. | textes normatifs divergents |

## Limites de preuve

[FAIT] Aucun service externe réel n’a été appelé pour cette revue.

[FAIT] Les branches distantes ont été inspectées à partir des références locales; aucun `fetch` n’a été effectué.

[HYPOTHÈSE] Des usages réels, incidents ou besoins connus du propriétaire peuvent invalider certaines priorités sans être visibles dans le dépôt.
