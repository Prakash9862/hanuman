# src/hanuman/services/notion_service.py

import logging

import httpx
from hanuman.core.config import get_env_var

logger = logging.getLogger(__name__)

NOTION_API_URL = "https://api.notion.com/v1/users/me"
NOTION_VERSION = "2022-06-28"


def ping_notion() -> dict:
    token = get_env_var("NOTION_TOKEN")

    if not token:
        logger.error("❌ Aucun token Notion fourni dans .env")
        return {"ok": False, "error": "Missing token"}

    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": NOTION_VERSION,
    }

    try:
        response = httpx.get(NOTION_API_URL, headers=headers, timeout=5)

        if response.status_code == 200:
            user = response.json()
            logger.info("🔌 Connexion à Notion réussie")
            return {"ok": True, "user": user}

        elif response.status_code == 401:
            logger.error("⛔ Token Notion invalide")
            return {"ok": False, "error": "Unauthorized"}

        else:
            logger.warning(f"⚠️ Réponse inattendue Notion : {response.status_code}")
            return {"ok": False, "error": f"Unexpected status: {response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"💥 Erreur lors de la requête Notion : {e}")
        return {"ok": False, "error": str(e)}
