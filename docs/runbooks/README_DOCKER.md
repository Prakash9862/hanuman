# 📦 README_DOCKER.md — Dockerisation du projet Hanuman (v2.0)

## 📁 Structure des fichiers Docker

```
.
├── Dockerfile                    # Fichier principal multi-stage (dev/prod)
├── docker-compose.yml           # Orchestration locale des services
├── .dockerignore                # Fichiers/dossiers exclus du build
└── scripts/
    ├── dev.sh                   # Script d’initialisation locale rapide
    └── docker-entrypoint.sh     # Script de lancement conditionnel (dev/test/prod)
```

---

## 🐳 Dockerfile (multi-stage)

### 🔹 Base commune

- `FROM python:3.12-slim`
- Installe `make`, `curl`, `git`
- Installe `poetry`
- `COPY` du `pyproject.toml` et `poetry.lock`
- `poetry install --no-root`

### 🔹 Stage dev

- `COPY . .`
- `COPY scripts/docker-entrypoint.sh`
- `ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]`
- `CMD` piloté par `APP_ENV=dev`

### 🔹 Stage prod

- Reprend la base
- Expose uniquement `src/` + `pyproject.toml`
- `CMD` = `uvicorn` sans `--reload`

---

## 📋 docker-compose.yml

### Service principal : `hanuman`

```yaml
services:
  hanuman:
    build:
      context: .
      target: dev
    volumes:
      - .:/app
      - ./logs:/app/logs
    ports:
      - "8000:8000"
    env_file:
      - .env
    environment:
      - APP_ENV=dev
```

---

## 🥃 .dockerignore

````
__pycache__/
*.pyc
*.pyo
*.pyd
*.log
.env
.git
.gitignore
logs/
.vscode/
*.md
.coverage
.pytest_cache/
.venv


---

## 🧠 EntryPoint conditionnel

`scripts/docker-entrypoint.sh` permet :

* `APP_ENV=dev`  → `make run` (Uvicorn avec reload)
* `APP_ENV=test` → `make test`
* `APP_ENV=prod` → `uvicorn` pur
* `DEBUG=true` → mode verbeux activé
* `exec "$@"` permet `docker run -it` sans shell bloqué

---

## 🔄 Scripts facilités

### scripts/dev.sh

```bash
#!/bin/bash

echo "🔧 [Hanuman Dev] Reconstruction de l’image..."
docker compose down

echo "🐳 [Hanuman Dev] Build de l’image Docker (target = dev)..."
docker compose build

echo "🌟 [Hanuman Dev] Démarrage du conteneur..."
docker compose up
````

---

## 🥪 Exécutions typiques

### Développement local

```bash
docker build -t hanuman-dev --target dev .
docker run --rm -v $(pwd):/app --env-file .env -e APP_ENV=dev hanuman-dev
```

### Tests CI ou local

```bash
docker run --rm --env-file .env -e APP_ENV=test hanuman-dev
```

### Production (mode sans reload)

```bash
docker run -d -p 8000:8000 --env-file .env -e APP_ENV=prod hanuman-dev
```

---

## ✅ Checklist de sécurité Docker

- [x] Aucun secret hardcodé dans l’image
- [x] Fichiers sensibles ignorés (.env, logs, etc.)
- [x] Mode reload limité à `dev`
- [x] `exec` PID 1 pour gestion propre des signaux
- [x] Entrypoint scripté, testable et versionable
- [x] Rotation des logs prise en charge via `structlog`

---

## 🧰 Outils disponibles dans l’image

- `poetry`
- `make`
- `curl`
- `git`
- `pytest`
- `ruff`, `mypy`, `black` (via `make lint`, `make typecheck`, etc.)

---

## 🐙 Intégration GitHub Actions ➔ DockerHub

### Secrets GitHub nécessaires

- `DOCKERHUB_USERNAME`
- `DOCKERHUB_TOKEN`

### Extrait de `.github/workflows/docker-publish.yml`

```yaml
- name: 🔐 Login DockerHub
  uses: docker/login-action@v3
  with:
    username: ${{ secrets.DOCKERHUB_USERNAME }}
    password: ${{ secrets.DOCKERHUB_TOKEN }}

- name: 🔧 Build & Push
  uses: docker/build-push-action@v5
  with:
    push: true
    tags: prakash9862/hanuman:latest
```

---

## 🔬 Tests depuis le conteneur

```bash
# Test total avec couverture
make test-cov

# Lancement interactif dans un shell debug
docker run -it --env-file .env -e APP_ENV=dev hanuman-dev bash
```

---

## 📦 Tagging des images

| Type            | Tag exemple  |
| --------------- | ------------ |
| Dernier build   | `:latest`    |
| Version stable  | `:v2.0.0`    |
| Dev local       | `:dev`       |
| Test temporaire | `:ci-[hash]` |

---

## 🧹 Extensions futures

- Ajout de `docker-compose.override.yml` pour profiling local
- Intégration d’un `Log Viewer` local à partir de `logs/`
- Support des workers asynchrones (via `celery`, `arq`, ou autre)
- Healthcheck HTTP auto dans `docker-compose.yml`

---

## 🏁 Conclusion

Le système Docker Hanuman v2.0 est **modulaire**, **professionnel**, **testable**, et prêt à être **déployé en environnement contrôlé**. Toutes les couches sont séparées proprement, les secrets exclus, les logs montés, et la CI intégrable directement dans GitHub Actions ou autre pipeline avancé.
