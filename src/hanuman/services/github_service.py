# src/hanuman/services/github_service.py

import logging

import httpx

from hanuman.core.config import get_env_var

logger = logging.getLogger(__name__)

GITHUB_API_URL = "https://api.github.com/user"


def ping_github() -> dict:
    token = get_env_var("GITHUB_TOKEN")

    if not token:
        logger.error("❌ Aucun token GitHub fourni dans .env")
        return {"ok": False, "error": "Missing token"}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json",
    }

    try:
        response = httpx.get(GITHUB_API_URL, headers=headers, timeout=5)

        if response.status_code == 200:
            user = response.json()
            logger.info("🟢 Connexion à GitHub réussie")
            return {"ok": True, "login": user.get("login")}

        elif response.status_code == 401:
            logger.error("⛔ Token GitHub invalide")
            return {"ok": False, "error": "Unauthorized"}

        else:
            logger.warning(f"⚠️ Réponse inattendue GitHub : {response.status_code}")
            return {"ok": False, "error": f"Unexpected status: {response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"💥 Erreur lors de la requête GitHub : {e}")
        return {"ok": False, "error": str(e)}
