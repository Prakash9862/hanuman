from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import httpx

from hanuman.core.config import settings
from hanuman.core.token_manager import load_token_json, save_token_json
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
CALENDAR_LIST_URL = "https://www.googleapis.com/calendar/v3/users/me/calendarList"
CALENDAR_EVENTS_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"


def _get_access_token() -> str:
    tokens = load_token_json("google_calendar")
    access_token = tokens.get("access_token")

    if not access_token:
        raise ValueError("Calendar non connecté : aucun access_token trouvé")

    return str(access_token)


def _authorization_headers() -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_access_token()}",
        "Accept": "application/json",
    }


@trace_endpoint("calendar", catch=True)
def exchange_code_for_token(code: str) -> bool:
    data = {
        "code": code,
        "client_id": settings.google_calendar_client_id,
        "client_secret": settings.google_calendar_client_secret,
        "redirect_uri": settings.google_calendar_redirect_uri,
        "grant_type": "authorization_code",
    }

    response = httpx.post(GOOGLE_TOKEN_URL, data=data, timeout=15)

    if response.status_code == 200:
        save_token_json("google_calendar", response.json())
        return True

    if response.status_code == 400:
        raise ValueError(f"Code OAuth expiré ou invalide : {response.text}")

    raise RuntimeError(f"Erreur OAuth Calendar : {response.status_code} {response.text}")


def get_calendars() -> list[dict[str, Any]]:
    response = httpx.get(
        CALENDAR_LIST_URL,
        headers=_authorization_headers(),
        timeout=15,
    )

    if response.status_code == 401:
        raise ValueError("Token Calendar expiré ou invalide")

    response.raise_for_status()

    calendars: list[dict[str, Any]] = []

    for item in response.json().get("items", []):
        calendars.append(
            {
                "id": item.get("id"),
                "summary": item.get("summary", "Calendrier sans nom"),
                "description": item.get("description"),
                "primary": bool(item.get("primary", False)),
                "access_role": item.get("accessRole"),
                "background_color": item.get("backgroundColor"),
            }
        )

    return calendars


def get_upcoming_events(
    max_results: int = 20,
) -> list[dict[str, Any]]:
    now = datetime.now(UTC).isoformat().replace("+00:00", "Z")

    params: dict[str, str | int] = {
        "timeMin": now,
        "maxResults": max(1, min(max_results, 100)),
        "singleEvents": "true",
        "orderBy": "startTime",
    }

    response = httpx.get(
        CALENDAR_EVENTS_URL,
        headers=_authorization_headers(),
        params=params,
        timeout=15,
    )

    if response.status_code == 401:
        raise ValueError("Token Calendar expiré ou invalide")

    response.raise_for_status()

    events: list[dict[str, Any]] = []

    for item in response.json().get("items", []):
        start = item.get("start", {})
        end = item.get("end", {})

        events.append(
            {
                "id": item.get("id"),
                "summary": item.get("summary", "Événement sans titre"),
                "description": item.get("description"),
                "location": item.get("location"),
                "start": start.get("dateTime") or start.get("date"),
                "end": end.get("dateTime") or end.get("date"),
                "all_day": "date" in start,
                "status": item.get("status"),
                "html_link": item.get("htmlLink"),
            }
        )

    return events


@trace_endpoint("calendar", catch=True)
def get_calendar_list() -> PingResult:
    calendars = get_calendars()

    return PingResult(
        ok=True,
        source="calendar",
        detail={"calendar_count": len(calendars)},
    )
