"""
env.py — Charge et expose toutes les variables d'environnement du projet Hanuman.

Ce module est la **source unique de vérité** pour :
- Tokens Notion
- Tokens GitHub
- Tokens OpenAI
- Google OAuth
- Paramètres généraux (log level, URLs…)
- Configuration interne à Hanuman

Tous les services (notion, github, orchestrations, ui…) doivent
importer leurs valeurs via ce module :

    from hanuman.config.env import NOTION_TOKEN, GITHUB_TOKEN

Ainsi, plus jamais de load_dotenv sauvage ailleurs dans le code.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# ---------------------------------------------------------------------------
# LOCALISATION DU .env
# ---------------------------------------------------------------------------

# On part de ce fichier : /hanuman/src/hanuman/config/env.py
# parents[0] = /hanuman/src/hanuman
# parents[1] = /hanuman/src
# parents[2] = /hanuman         ✅ racine du projet
ROOT_DIR = Path(__file__).resolve().parents[3]
ENV_PATH = ROOT_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    # On NE bloque PAS les tests, on prévient seulement
    print(f"⚠️  [env] .env introuvable à l'emplacement attendu : {ENV_PATH}")


# ---------------------------------------------------------------------------
# NOTION
# ---------------------------------------------------------------------------

NOTION_TOKEN: str | None = os.environ.get("NOTION_TOKEN")
NOTION_VERSION: str = os.environ.get("NOTION_VERSION", "2025-09-03")

# ID d’une database ou page selon usage
NOTION_PARENT_ID: str | None = os.environ.get("NOTION_PARENT_ID")
NOTION_ISSUES_DB_ID: str | None = os.environ.get("NOTION_ISSUES_DB_ID")
NOTION_PARENT_PAGE_ID: str | None = os.environ.get("NOTION_PARENT_PAGE_ID")
NOTION_PROJECT_MEMORY_PARENT_PAGE_ID: str | None = os.environ.get(
    "NOTION_PROJECT_MEMORY_PARENT_PAGE_ID"
)

# ---------------------------------------------------------------------------
# GITHUB
# ---------------------------------------------------------------------------

GITHUB_TOKEN: str | None = os.environ.get("GITHUB_TOKEN")
GITHUB_REPO: str | None = os.environ.get("GITHUB_REPO")  # ex: "Prakasch9862/hanuman"
GITHUB_ALLOWED_REPOSITORIES: tuple[str, ...] = tuple(
    repository.strip()
    for repository in os.environ.get("GITHUB_ALLOWED_REPOSITORIES", "").split(",")
    if repository.strip()
)
GITHUB_PROJECT_MEMORY_REPOSITORY: str = os.environ.get(
    "GITHUB_PROJECT_MEMORY_REPOSITORY", "Prakash9862/hanuman"
)
GITHUB_PROJECT_MEMORY_BRANCH: str = os.environ.get("GITHUB_PROJECT_MEMORY_BRANCH", "main")

# ---------------------------------------------------------------------------
# OPENAI
# ---------------------------------------------------------------------------

OPENAI_API_KEY: str | None = os.environ.get("OPENAI_API_KEY")

# ---------------------------------------------------------------------------
# GOOGLE OAUTH
# ---------------------------------------------------------------------------

GOOGLE_CLIENT_ID: str | None = os.environ.get("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET: str | None = os.environ.get("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI: str | None = os.environ.get("GOOGLE_REDIRECT_URI")

# ---------------------------------------------------------------------------
# PARAMÈTRES GÉNÉRAUX
# ---------------------------------------------------------------------------

APP_ENV: str = os.environ.get("APP_ENV", "dev")
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
BASE_URL: str = os.environ.get("BASE_URL", "http://127.0.0.1:8000")

# Échecs
CHESS_COM_USERNAME: str | None = os.environ.get("CHESS_COM_USERNAME")


def chess_player_name() -> str:
    """Retourne le joueur Chess configuré pour toutes les analyses Hanuman."""

    player_name = (CHESS_COM_USERNAME or "").strip()
    if not player_name:
        raise RuntimeError("CHESS_COM_USERNAME manquant dans la configuration Hanuman")
    return player_name


# ---------------------------------------------------------------------------
# CHECK OPTIONNEL DES VALEURS CRITIQUES
# ---------------------------------------------------------------------------

CRITICAL_VARS = {
    "NOTION_TOKEN": NOTION_TOKEN,
    "GITHUB_TOKEN": GITHUB_TOKEN,
    "OPENAI_API_KEY": OPENAI_API_KEY,
}

for key, value in CRITICAL_VARS.items():
    if value in (None, "", "null"):
        print(f"⚠️  [env] Attention : {key} n'est pas configurée.")
