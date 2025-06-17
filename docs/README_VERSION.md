# Hanuman - Plan de Version 2.0 (Stabilisation Environnementale)

## Objectif principal

> Finaliser une version **locale, stable, professionnelle et durable** de l’API Hanuman, sans ajout de logique métier, mais avec **toutes les fondations techniques figées** : structure de code, logs, tests, sécurité, config, outils dev, CI.

---

## 📅 État actuel : `v2.3` (structlog)

### ✅ Tâches accomplies :

* Intégration initiale de `structlog`
* Décorateurs de log (`@log_ping`)
* Logger contextualisé

### ❌ Reste à faire pour finaliser `v2.3.1` :

* [ ] Ajout `hanuman_error.log` + `hanuman_debug.log` séparés
* [ ] Logging JSON (prod) / coloré (dev)
* [ ] Middleware de logging HTTP

---

## 🔮 `v2.4` — Testabilité & Couverture

* [ ] Convention uniforme de test `ok / error`
* [ ] Edge case tests : token manquant, endpoint invalide, fichier manquant
* [ ] Ajout de `pytest-cov` + badge
* [ ] `tests/conftest.py` avec fixtures
* [ ] Rapport HTML de couverture

---

## 🔐 `v2.5` — Sécurité & Auth

* [ ] Middleware de tokenisation (`X-Hanuman-Token`)
* [ ] Refus HTTP 401 si token absent/erroné
* [ ] `.env` + `.env.example` avec token obligatoire
* [ ] Option de whitelist IP (127.0.0.1)
* [ ] Aucun endpoint libre sauf `/status`

---

## 🧹 `v2.6` — Configuration & Nettoyage

* [ ] Centralisation des chemins dans `config.py`
* [ ] `hanuman_config.json` lu dynamiquement
* [ ] Script `scripts/check_env.py`
* [ ] Nettoyage `pyproject.toml`
* [ ] Ajout `.env.example`

### Documentation interne

* [ ] `docs/README_STRUCTURE.md`
* [ ] `docs/README_LOGS.md`
* [ ] `docs/README_ENV.md`
* [ ] Export `docs/openapi.json`

---

## ⚙️ `v2.7` — Outils de développement & CI

* [ ] `Makefile` : lint / test / coverage / docker
* [ ] `pre-commit` : black, mypy, ruff, pytest, isort
* [ ] `make install-hooks`
* [ ] GitHub Actions : lint + test + coverage badge

---

## 🛥️ `v2.8` — Dockerisation locale

* [ ] Dockerfile pour environnement local
* [ ] docker-compose.yml si services tiers
* [ ] Intégration Makefile : `make docker`, `make docker-up`

---

## 🌟 `v2.9` — Consolidation finale

* [ ] Création endpoint `/health`
* [ ] Listing de tous les endpoints actifs
* [ ] README.md à jour
* [ ] Freeze de la structure : figée pour future v3
* [ ] Export final docs (structure, openapi, convention, conf)

---

## 🏁 Hanuman `v3.0` — Ouverture vers les modules métiers

> Aucune logique métier ne sera intégrée avant la validation complète de la v2.0.


---


🧱 Ce que l’on va FAIRE CONCRÈTEMENT pour intégrer structlog dans Hanuman
1. 📁 Créer un nouveau fichier core/logging.py

Structure recommandée :

    get_logger(name: Optional[str]) → retourne un logger structlog

    configure_logging() → à appeler une seule fois dans main.py

    Deux renderers :

        ConsoleRenderer() si dev (DEBUG)

        JSONRenderer() si prod (INFO+)

    Configuration des handlers :

        hanuman_debug.log (text)

        hanuman_error.log (JSON)

        stdout coloré ou silencieux selon config

2. 🔁 Modifier l’appel de log dans tout le projet
Avant (standard)	Après (structlog)
import logging	import structlog
logger = logging.getLogger(__name__)	logger = get_logger(__name__)
logger.info(...)	logger.info(...) + .bind(...)
Modules à modifier :

    main.py

    api/*.py

    services/*.py

    Tous les tests si loggés

    utils/helpers.py (s’il y a du print ou log implicite)

3. 🧩 Modifier ou créer un décorateur @log_request ou @log_ping

    Ajout automatique de :

        Nom de route

        IP source (request.client.host)

        Timestamp

        Token partiel (si présent)

        Statut de réponse

→ On remplace l’ancien @log_ping si besoin.
4. 📁 Créer / Modifier la structure des fichiers logs

/logs/hanuman_debug.log (niveau DEBUG+, texte lisible)

/logs/hanuman_error.log (niveau ERROR+, format JSON)

    (optionnel) /logs/hanuman_request.log (si on veut journaliser les requêtes)

Il faudra :

    Créer les fichiers à vide dans Git (.gitkeep)

    Ajouter les handlers dans logging.FileHandler(...)

5. 🧪 Adapter ou créer un test pour les logs

    Vérifier qu’un appel à /status produit bien un log structuré

    Vérifier la présence de certaines clés (event, ip, status_code)

    Tester que les logs sont bien différents en dev et en prod

6. ⚙️ Modifier le Makefile si besoin

    Ajouter une commande utile type :

make logs       # affiche les logs en live (tail -f)
make log-debug  # affiche les logs DEBUG

7. 🧼 Nettoyer l’existant

    Supprimer :

        config/logging.yaml (plus nécessaire avec structlog)

        Toutes les références à logging.basicConfig(...)

    Mettre à jour .gitignore :

    logs/hanuman_debug.log
    logs/hanuman_error.log

8. 📓 Documenter la stratégie

Créer un fichier :

docs/README_LOGS.md

Avec :

    Niveau de log

    Localisation des fichiers

    Différence dev/prod

    Comment logger dans un service proprement

    Comment ajouter un contexte (.bind())

✅ Résumé : impact total sur l’arborescence

src/hanuman/
├── core/
│   └── logging.py         # 💥 Nouveau
├── api/
│   └── status.py          # 🔁 get_logger()
├── services/
│   └── notion_service.py  # 🔁 get_logger()
tests/
├── test_logging.py        # 💥 Nouveau
logs/
├── hanuman_debug.log      # 💥 Nouveau
├── hanuman_error.log      # 💥 Nouveau
config/
├── logging.yaml           # ❌ À supprimer
docs/
├── README_LOGS.md         # 💥 Nouveau

---

# Structlog - Plan d'amélioration avancée Hanuman

## ⚠️ 0. Harmonisation des erreurs

Avant toute chose, on constate **de nombreuses erreurs mypy (16 erreurs / 11 fichiers)**
liées à :

* des `None` non typés dans les objets `Request`
* des retours sans annotation
* des signatures manquantes dans les wrappers
* des mauvaises signatures dans les `bind()`

### 🔧 Objectif

Mettre en place une **stratégie d’harmonisation de la typage et des interfaces loguées** :

* typage propre de `Request` dans les décorateurs
* typage des `return` pour toutes les fonctions — même les lambdas ou wrappers
* mise en place d’un linter typographique stricte
* éventuellement, wrapper structlog dans une interface typée maison

---

## 🌐 1. Ajout de contexte enrichi dans les logs

### 📄 Actuel :

Les logs enrichissent l’appel avec :

* `ip`
* `endpoint`
* `method`
* `debug_mode`

### ✅ À faire :

* Ajouter : `user_id`, `source`, `token_prefix`, `platform`, `agent`, `lang`, `session_id`
* Tous les `logger.bind(...)` pourront être faits une seule fois via une fonction `build_context(request: Request) -> dict`

---

## 🎨 2. Loguer les retours de fonction (optionnel)

### ✅ À faire :

* Ajouter un argument à `@trace_endpoint(..., log_return=True)`
* Si activé : logguer le `result` en `DEBUG`, uniquement s’il est de type éligible (PingResult, dict, str...)
* Ajout d’un `truncate_long_values(result)` pour éviter les dump illisibles

---

## 🔧 3. Test structlog avec caplog

### 📄 Objectif : valider que les logs sont bien produits

* [ ] Écrire un test `test_trace_logging()` avec `caplog`
* [ ] Appeler une fonction de service logguée
* [ ] Vérifier qu’au moins une ligne contient :

  * `"Requête reçue"`
  * `"Exécution réussie"` ou `"Erreur ... dans ..."`

---

## 🔢 4. Rotation et nettoyage des logs

### ✅ À faire :

* Ajouter un handler `TimedRotatingFileHandler` dans `logging.py`
* Gérer la rotation de `hanuman_debug.log` tous les 7 jours, 4 fichiers max
* Ajouter une suppression automatique des logs > 28 jours (cron ou script manuel ?)

---

## 📃 5. Documenter la stratégie

### 🔖 Fichier `docs/README_LOGS.md`

Contenu attendu :

* niveaux utilisés (DEBUG, INFO, ERROR)
* conventions sur le bind
* exemple de JSON produit
* structure des fichiers `.log`
* comment lire / filtrer les logs (grep, jq, Loki ?)

---
