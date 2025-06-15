from fastapi import FastAPI
from fastapi.routing import APIRoute

from hanuman.api import chess_com, github, notion, obsidian, openai, status
from hanuman.core.logging import setup_logging

# Initialisation du logger
logger = setup_logging()
logger.info("🚀 Lancement de Hanuman API")

# Création de l'app FastAPI
app = FastAPI(
    title="Hanuman API",
    version="1.1.0",
    description="API personnelle d’orchestration modulaire",
)

# Inclusion des routes
app.include_router(status.router)
app.include_router(notion.router)
app.include_router(github.router)
app.include_router(chess_com.router)
app.include_router(obsidian.router)
app.include_router(openai.router)

# 🔍 Log intelligent de fin d'initialisation
active_routes = [r.path for r in app.routes if isinstance(r, APIRoute)]
logger.info("✅ Hanuman initialisé – main.py exécuté jusqu’au bout")
logger.info(f"📦 Routes actives : {active_routes}")
