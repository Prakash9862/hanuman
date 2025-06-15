# src/hanuman/services/calendar_service.py

import logging

import httpx

from hanuman.core.config import get_env_var
from hanuman.core.token_manager import load_token_json, save_token_json

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"


def exchange_code_for_token(code: str) -> bool:
    data = {
        "code": code,
        "client_id": get_env_var("GOOGLE_CLIENT_ID"),
        "client_secret": get_env_var("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": get_env_var("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }

    try:
        response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=10)
        if response.status_code == 200:
            token_data = response.json()
            save_token_json("google_calendar", token_data)
            logger.info("✅ Token Google Calendar reçu et stocké")
            return True
        else:
            logger.error(f"❌ Erreur lors de l’échange : {response.text}")
            return False
    except Exception as e:
        logger.error(f"💥 Exception Google Calendar token exchange : {e}")
        return False


def get_calendar_list() -> dict:
    tokens = load_token_json("google_calendar")
    access_token = tokens.get("access_token")

    if not access_token:
        return {"ok": False, "error": "No access_token found"}

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = httpx.get(CALENDAR_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            logger.info("📆 Calendrier récupéré avec succès")
            return {"ok": True, "calendar_count": len(data.get("items", []))}

        elif response.status_code == 401:
            return {"ok": False, "error": "Token expiré ou invalide"}

        else:
            return {"ok": False, "error": f"Erreur HTTP {response.status_code}"}
    except Exception as e:
        logger.error(f"💥 Erreur Google Calendar : {e}")
        return {"ok": False, "error": str(e)}
