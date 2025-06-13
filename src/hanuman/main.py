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

# Message de démarrage
logger.info("✅ API initialisée avec succès")
