# src/hanuman/services/calendar_service.py

import logging

import httpx

from hanuman.core.config import get_env_var
from hanuman.core.token_manager import load_token_json, save_token_json
from hanuman.models.ping import PingResult  # ✅ Ajouté

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


def get_calendar_list() -> PingResult:
    tokens = load_token_json("google_calendar")
    access_token = tokens.get("access_token")

    if not access_token:
        return PingResult(ok=False, source="calendar", error="No access_token found")

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    try:
        response = httpx.get(CALENDAR_API_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            return PingResult(
                ok=True,
                source="calendar",
                detail={"calendar_count": len(data.get("items", []))},
            )

        elif response.status_code == 401:
            return PingResult(ok=False, source="calendar", error="Token expiré ou invalide")

        else:
            return PingResult(
                ok=False, source="calendar", error=f"Erreur HTTP {response.status_code}"
            )
    except Exception as e:
        logger.error(f"💥 Erreur Google Calendar : {e}")
        return PingResult(ok=False, source="calendar", error=str(e))
