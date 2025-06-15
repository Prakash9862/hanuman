# src/hanuman/services/chess_service.py

import logging

import httpx

logger = logging.getLogger(__name__)

CHESS_USERNAME = "prakash9862"  # à terme à rendre dynamique
CHESS_API_URL = f"https://api.chess.com/pub/player/{CHESS_USERNAME}"


def ping_chess() -> dict:
    try:
        response = httpx.get(CHESS_API_URL, timeout=5)

        if response.status_code == 200:
            user = response.json()
            logger.info("♟️ Connexion à Chess.com réussie")
            return {"ok": True, "username": user.get("username", None)}

        elif response.status_code == 404:
            logger.warning("🚫 Utilisateur Chess.com introuvable")
            return {"ok": False, "error": "User not found"}

        else:
            logger.warning(f"⚠️ Réponse inattendue Chess.com : {response.status_code}")
            return {"ok": False, "error": f"Unexpected status: {response.status_code}"}

    except httpx.RequestError as e:
        logger.error(f"💥 Erreur Chess.com : {e}")
        return {"ok": False, "error": str(e)}
