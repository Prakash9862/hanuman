# HANUMAN — Rapport de nuit

## 1. Résumé exécutif

Hanuman conserve son architecture, ses contrats publics et son comportement applicatif.
L’état Git initial était propre sur la branche dédiée `codex/night-coverage-stability`.
La collecte pytest trouve 160 tests, mais tout appel `TestClient` se suspend dans cet
environnement, y compris avec une application FastAPI minimale indépendante de Hanuman.
Le sous-ensemble déterministe sans `TestClient` est passé de 122 à 133 tests réussis.
Onze tests isolés ont été ajoutés autour du connecteur Gmail, sans appel réseau ni OAuth réel.
Sur le périmètre exécutable identique, la couverture globale progresse de 67 % à 70 %, et
`hanuman.core.gmail` de 24 % à 80 %. Ruff, mypy et le build frontend passent.
Le niveau de confiance est élevé pour les tests ajoutés, mais la suite HTTP complète reste
bloquée par l’environnement de test local.

## 2. État initial

- Branche : `codex/night-coverage-stability`.
- État Git : propre (`git status --short`, `git diff --stat` et `git diff` sans sortie).
- Changements préexistants : aucun.
- Commandes disponibles : `make test`, `make coverage`, `make format-check`, `make lint`,
  `make typecheck`, `make check`, `make all-check`; frontend `npm run build`.
- Outils : pytest 8.4.0, coverage/pytest-cov, Black, Ruff, mypy, FastAPI, Vite et TypeScript.
- Collecte initiale : 160 tests en 0,20 s, sans erreur de collecte.
- Suite complète initiale : bloquée sur le premier appel HTTP
  (`tests/api/test_calendar.py::test_calendar_auth_redirect`), interrompue après environ
  deux minutes; reproduction ciblée arrêtée par délai après 40 s.
- Sous-ensemble initial sans fichiers utilisant `TestClient` : 122 réussis, 0 échec,
  0 ignoré, 2 avertissements, en 0,48 s (3,28 s processus inclus).
- Couverture initiale mesurable sur ce sous-ensemble : 67 % (2 040/3 036 instructions).
- Erreurs initiales : aucune erreur de test sur le périmètre exécutable; deux avertissements
  Pydantic sur `datetime.utcnow()`; blocage `TestClient`.

## 3. Tests

| Suite       | Avant | Après | Résultat |
| ----------- | ----: | ----: | -------- |
| Backend     | 122 réussis | 133 réussis | Périmètre sans `TestClient`, stable |
| Frontend    | Non mesuré | Non mesuré | Aucune suite de tests déclarée; build réussi |
| Intégration | Non mesuré | Non mesuré | Appels `TestClient` bloqués |
| Autres      | 160 collectés | 171 collectés | 0 erreur de collecte |

- Avant : 122 réussis, 0 échoué, 0 ignoré, 2 avertissements sur le périmètre exécutable.
- Après : 133 réussis, 0 échoué, 0 ignoré, 2 avertissements sur le même périmètre.
- Suite complète finale : délai de 15 s atteint sans résultat, comme à l’état initial.
- Les 38 tests présents dans les 14 fichiers utilisant `TestClient` n’ont pas reçu de
  verdict pass/fail dans cet environnement.

## 4. Couverture

- Couverture globale avant : 67 % (périmètre exécutable sans `TestClient`).
- Couverture globale après : 70 % sur le même périmètre.
- Différence : +3 points, soit 79 instructions supplémentaires couvertes.
- Module amélioré : `src/hanuman/core/gmail.py`, de 24 % à 80 %.
- Zones toujours faibles : `wikipedia_qa_openai.py` (0 %),
  `obsidian_to_notion_safe.py` (24 %), `resources_service.py` (29 %), plusieurs routes API
  entre 38 % et 64 %, et `obsidian_notion_dashboard.py` (43 %).
- Les routes n’ont pas été davantage testées car la pile `TestClient` locale se bloque.
  Les parcours OAuth et services externes réels ont été volontairement exclus.
- Obsidian → Notion était déjà couvert à 90 % sur le périmètre mesuré; ses scénarios de
  parsing, Unicode implicite via UTF-8, fichier absent et erreurs Notion simulées existaient.

## 5. Tests ajoutés

- Fichier : `tests/core/test_gmail.py`.
- Comportements vérifiés : priorité des credentials d’environnement, lecture d’un fichier
  credentials temporaire, configuration absente, jeton absent ou malformé, sauvegarde avec
  expiration et permissions `0600`, rafraîchissement de jeton expiré, absence de
  `refresh_token`, erreur HTTP 401 simulée, décodage Unicode d’un corps MIME imbriqué,
  références de messages malformées, pagination et plafonnement, états non configuré et
  déconnecté.
- Raison : Gmail ne disposait d’aucun test unitaire dédié et constituait une zone métier
  importante à 24 % de couverture.
- Dépendances simulées : `urllib.request.urlopen`, `_json_request`, `_api`, `_credentials`,
  `_load_token` et `_save_token`; les fichiers sont limités à `tmp_path`.
- Valeur réelle : protection des erreurs de configuration, de token et de réponses externes
  sans authentification, réseau, secret réel ni modification des données utilisateur.

## 6. Bugs corrigés

Aucun bug certain n’a été corrigé.

Le blocage HTTP est reproductible, mais une application FastAPI minimale utilisant les mêmes
dépendances se bloque également. Il est donc classé comme problème d’environnement ou de
compatibilité de la pile de test, et non corrigé artificiellement dans le code Hanuman.

## 7. Fichiers modifiés

- `tests/core/test_gmail.py` : ajoute onze tests unitaires déterministes du connecteur Gmail.
- `docs/CODEX_NIGHT_REPORT.md` : consigne l’audit, les mesures, les limites et le verdict.

## 8. Commandes exécutées

- `git branch --show-current` → `codex/night-coverage-stability`.
- `git status --short`, `git diff --stat`, `git diff` → état initial propre.
- `poetry run pytest --collect-only -q` → 160 tests initiaux collectés en 0,20 s.
- `poetry run pytest -q -ra` → bloqué; interruption après environ deux minutes.
- `timeout 40s poetry run pytest -vv -x` → blocage identifié au premier test Calendar.
- Test FastAPI minimal avec `TestClient` et délai de 12 s → blocage reproduit hors Hanuman.
- `poetry run pytest -q -ra` avec 14 fichiers `TestClient` ignorés → 122 réussis avant,
  puis 133 réussis après; 2 avertissements dans les deux cas.
- `poetry run coverage run --source=src/hanuman -m pytest -q` sur ce même périmètre,
  puis `poetry run coverage report -m` → 67 % avant, 70 % après.
- `poetry run pytest -q -ra tests/core/test_gmail.py` → 11 réussis en 0,06 s.
- `poetry run ruff check .` → réussi avant et après.
- `poetry run mypy src/hanuman tests` → réussi avant (121 fichiers) et après (122 fichiers).
- `npm --prefix frontend run build` → réussi avant et après.
- `poetry run black --check .` → échec final sur quatre fichiers préexistants non modifiés.
- `poetry run black --check tests/core/test_gmail.py` → réussi.
- `timeout 15s poetry run pytest -q -ra` → délai final atteint, cohérent avec l’état initial.
- `git diff --check` → réussi avant création du présent rapport.

## 9. Éléments volontairement non modifiés

- Architecture et séparation routes/orchestrations/services/connecteurs.
- API publiques, signatures, formats de réponses et contrats frontend/backend.
- Routes FastAPI.
- Credentials, `.env`, tokens, secrets et identifiants externes.
- Configuration Notion, chemin du vault Obsidian et données utilisateur.
- Dépendances Python/Node, lockfiles et gestionnaires de paquets.
- Frontend et artefacts de build suivis.
- Code de production : aucun fichier applicatif modifié.
- Services externes : aucun appel réel, aucune synchronisation, aucune authentification.

## 10. Risques et blocages

- Critique : aucun.
- Élevé : aucun.
- Modéré : la suite HTTP complète est inexploitable localement car `TestClient` se suspend;
  38 tests existants n’ont donc pas pu être validés durant cette mission.
- Modéré : la couverture globale reste sous le seuil Makefile de 90 %; ce seuil n’était déjà
  pas atteint sur le périmètre mesurable.
- Faible : deux avertissements annoncent la dépréciation de `datetime.utcnow()` via Pydantic.
- Faible : Black signale quatre fichiers préexistants non conformes
  (`tests/api/test_connectors.py`, `src/hanuman/services/local_programs_service.py`,
  `src/hanuman/api/routers/resources.py`, `src/hanuman/services/resources_service.py`);
  ils n’ont pas été reformattés pour éviter des changements hors mission.

## 11. Questions ouvertes

- Le propriétaire souhaite-t-il figer ou réaligner les versions FastAPI/Starlette/httpx/anyio
  dans une intervention dédiée afin de diagnostiquer le blocage `TestClient` sur cette machine ?
- Le seuil de couverture Makefile de 90 % représente-t-il une exigence actuelle ou un objectif
  futur, compte tenu de la couverture mesurée à 70 % ?

## 12. Prochaines étapes recommandées

1. Reproduire le blocage `TestClient` dans un environnement CI propre et relever les versions
   exactes FastAPI, Starlette, httpx et anyio.
2. Une fois le client HTTP rétabli, relancer les 171 tests sans exclusions et recalculer la
   couverture complète.
3. Ajouter des tests isolés à `obsidian_to_notion_safe.py`, notamment vault absent, fichier
   illisible, parent Notion manquant et erreur Notion simulée.
4. Couvrir les fonctions restantes de Gmail : URL d’autorisation, échange de code et détail
   complet d’un message, toujours avec doubles contrôlés.
5. Traiter séparément les quatre écarts Black préexistants après validation du propriétaire.

## 13. Verdict

ORANGE — Les changements sont utiles mais certains points exigent une revue attentive.
