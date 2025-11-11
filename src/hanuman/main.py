import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env", override=True)

from fastapi import FastAPI
from fastapi.routing import APIRoute

from hanuman.api.core import (
    calendar,
    chess_com,
    github,
    notion,
    obsidian,
    openai,
    wikipedia,
)
from hanuman.api.orchestrations import (
    github_sync_notion,
    obsidian_to_notion,
    status,
)
from hanuman.core.logging import configure_logging, get_logger
from hanuman.core.middleware import log_requests

# Initialisation du système de logs
configure_logging()
logger = get_logger(__name__)
logger.info("🚀 Lancement de Hanuman API")


# Création de l'app FastAPI
app = FastAPI(
    title="Hanuman API",
    version="1.1.0",
    description="API personnelle d’orchestration modulaire",
)
app.middleware("http")(log_requests)

# Inclusion des routes
app.include_router(status.router)
app.include_router(notion.router)
app.include_router(github.router)
app.include_router(chess_com.router)
app.include_router(obsidian.router)
app.include_router(openai.router)
app.include_router(wikipedia.router)
app.include_router(calendar.router)
app.include_router(github_sync_notion.router)
app.include_router(obsidian_to_notion.router)

# 🔍 Log intelligent de fin d'initialisation
active_routes = [r.path for r in app.routes if isinstance(r, APIRoute)]
logger.info("✅ Hanuman initialisé – main.py exécuté jusqu’au bout")
logger.info(f"📦 Routes actives : {active_routes}")
