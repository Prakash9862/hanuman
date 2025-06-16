# src/hanuman/services/calendar_service.py

import httpx

from hanuman.core.config import get_env_var
from hanuman.core.token_manager import load_token_json, save_token_json
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_API_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"


@trace_endpoint("calendar", catch=True)
def exchange_code_for_token(code: str) -> bool:
    data = {
        "code": code,
        "client_id": get_env_var("GOOGLE_CLIENT_ID"),
        "client_secret": get_env_var("GOOGLE_CLIENT_SECRET"),
        "redirect_uri": get_env_var("GOOGLE_REDIRECT_URI"),
        "grant_type": "authorization_code",
    }

    response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=10)

    if response.status_code == 200:
        token_data = response.json()
        save_token_json("google_calendar", token_data)
        return True

    elif response.status_code == 400:
        raise ValueError("Code expiré ou invalide")

    raise RuntimeError(f"Erreur OAuth: {response.status_code} {response.text}")


@trace_endpoint("calendar", catch=True)
def get_calendar_list() -> PingResult:
    tokens = load_token_json("google_calendar")
    access_token = tokens.get("access_token")

    if not access_token:
        return PingResult(ok=False, source="calendar", error="No access_token found")

    headers = {
        "Authorization": f"Bearer {access_token}",
    }

    response = httpx.get(CALENDAR_API_URL, headers=headers, timeout=10)

    if response.status_code == 200:
        data = response.json()
        return PingResult(
            ok=True,
            source="calendar",
            detail={"calendar_count": len(data.get("items", []))},
        )

    elif response.status_code == 401:
        raise ValueError("Token expiré ou invalide")

    raise RuntimeError(f"Erreur API Calendar : {response.status_code}")
