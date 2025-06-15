# src/hanuman/services/openai_service.py

import logging

import httpx

from hanuman.core.config import get_env_var

logger = logging.getLogger(__name__)
OPENAI_API_URL = "https://api.openai.com/v1/models"


def ping_openai() -> dict:
    token = get_env_var("OPENAI_TOKEN")

    if not token:
        logger.error("❌ Aucun token OpenAI fourni dans .env")
        return {"ok": False, "error": "Missing token"}

    headers = {
        "Authorization": f"Bearer {token}",
    }

    try:
        response = httpx.get(OPENAI_API_URL, headers=headers, timeout=5)

        if response.status_code == 200:
            models = response.json()
            logger.info("🧠 Connexion à OpenAI réussie")
            return {"ok": True, "model_count": len(models.get("data", []))}

        elif response.status_code == 401:
            logger.error("⛔ Token OpenAI invalide")
            return {"ok": False, "error": "Unauthorized"}

        else:
            logger.warning(f"⚠️ Réponse inattendue OpenAI : {response.status_code}")
            return {"ok": False, "error": f"Unexpected status: {response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"💥 Erreur lors de la requête OpenAI : {e}")
        return {"ok": False, "error": str(e)}
