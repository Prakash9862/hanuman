############################
# 🔹 STAGE 1 — Base commune
############################
FROM python:3.12-slim AS base

# 👉 Argument d’environnement (prod/dev)
ARG YOUR_ENV=development
ENV YOUR_ENV=${YOUR_ENV}

# 👉 Config environnement Python et Poetry
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    POETRY_HOME="/opt/poetry" \
    PATH="$POETRY_HOME/bin:$PATH"

# 👉 Dépendances système essentielles
RUN apt-get update && apt-get install -y \
    curl \
    git \
    make \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 👉 Installer Poetry (version verrouillée)

ENV POETRY_HOME="/root/.local"
ENV PATH="$POETRY_HOME/bin:$PATH"

RUN curl -sSL https://install.python-poetry.org | python3 -

# 👉 Dossier temporaire pour build isolé
WORKDIR /tmp/build
COPY pyproject.toml poetry.lock ./

RUN mkdir -p /install && cp pyproject.toml poetry.lock /install/ && cd /install && poetry install --with dev --no-ansi --no-root

# 👉 Dossier de travail réel
WORKDIR /app

#############################
# 🔹 STAGE 2 — Dev complet
#############################
FROM base AS dev

# 👉 Créer le dossier de logs explicitement (au cas où volume)
RUN mkdir -p /app/logs

# 👉 Copier tout le reste du projet
COPY . .

# 👉 Rendre le script entrypoint exécutable
RUN chmod +x /app/scripts/docker-entrypoint.sh

# 👉 Définir l’entrée du conteneur
ENTRYPOINT ["/app/scripts/docker-entrypoint.sh"]

#############################
# 🔹 STAGE 3 — Prod allégée
#############################
FROM base AS prod

# 👉 Copier uniquement le strict nécessaire
COPY . .

# 👉 Supprimer tests et fichiers inutiles en prod (optionnel)
RUN rm -rf tests scripts/docker-entrypoint.sh .git .github

# 👉 Entrée du conteneur production (par exemple gunicorn/uvicorn)
ENTRYPOINT ["poetry", "run", "python", "src/hanuman/main.py"]
