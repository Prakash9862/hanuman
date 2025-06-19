# =======================
# 🟩 STAGE 1 — Base
# =======================
FROM python:3.12-slim AS base

WORKDIR /app

# Variables d'env minimales
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dépendances système de base
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    make \
    && rm -rf /var/lib/apt/lists/*

# Installer Poetry
ENV POETRY_VERSION=1.8.2
RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

# Copier les fichiers de dépendances
COPY pyproject.toml poetry.lock ./

# Installer les dépendances (sans le code)
RUN poetry install --no-root --no-interaction

# Copier le code (peut être évité en dev via volume)
COPY src/ ./src/
COPY Makefile ./
COPY config/ ./config/

# =======================
# 🟦 STAGE 2 — Dev
# =======================
FROM base AS dev

# Créer le dossier logs (monté si volume local)
RUN mkdir -p /app/logs

# Copier les scripts
COPY scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
RUN chmod +x /app/scripts/docker-entrypoint.sh

# Entrée interactive par défaut (modifiable)
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

# =======================
# 🟥 STAGE 3 — Prod
# =======================
FROM base AS prod

# Pas de --reload, pas de make, pas de test
COPY scripts/docker-entrypoint.sh /app/scripts/docker-entrypoint.sh
RUN chmod +x /app/scripts/docker-entrypoint.sh

ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]
