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
