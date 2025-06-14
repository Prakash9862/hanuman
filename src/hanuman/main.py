# src/hanuman/main.py

from fastapi import FastAPI

from hanuman.api import status
from hanuman.core.logging import setup_logging

# Initialisation du logger
logger = setup_logging()
logger.info("🚀 Lancement de Hanuman API")

# Création de l'app FastAPI
app = FastAPI(
    title="Hanuman API",
    version="0.1.0",
    description="API personnelle d’orchestration modulaire",
)

# Inclusion des routes
app.include_router(status.router)

# 🔍 Log intelligent de fin d'initialisation
from fastapi.routing import APIRoute

# On extrait les routes FastAPI activées (hors openapi et docs auto)
active_routes = [r.path for r in app.routes if isinstance(r, APIRoute)]

logger.info("✅ Hanuman initialisé – main.py exécuté jusqu’au bout")
logger.info(f"📦 Routes actives : {active_routes}")
