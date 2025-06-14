import logging
import os

from dotenv import load_dotenv

load_dotenv()  # charge le .env

logger = logging.getLogger(__name__)  # récupère le logger du module

# ✅ Si DEBUG est actif dans .env, loggue une ligne
if os.getenv("DEBUG", "false") == "true":
    logger.info("🔐 .env chargé (DEBUG=true)")


def get_env_var(key: str, default: str = "") -> str:
    """
    Récupère une variable d'environnement (depuis .env ou système).
    """
    return os.getenv(key, default)
