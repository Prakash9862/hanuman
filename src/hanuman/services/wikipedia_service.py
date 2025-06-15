# src/hanuman/services/wikipedia_service.py

import logging

import httpx

logger = logging.getLogger(__name__)
WIKIPEDIA_URL = "https://fr.wikipedia.org/api/rest_v1/page/summary/OpenAI"


def ping_wikipedia() -> dict:
    try:
        response = httpx.get(WIKIPEDIA_URL, timeout=5)

        if response.status_code == 200:
            data = response.json()
            logger.info("📚 Connexion à Wikipedia réussie")
            return {"ok": True, "title": data.get("title")}

        else:
            logger.warning(f"⚠️ Réponse inattendue Wikipedia : {response.status_code}")
            return {"ok": False, "error": f"Unexpected status: {response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"💥 Erreur lors de la requête Wikipedia : {e}")
        return {"ok": False, "error": str(e)}
