from __future__ import annotations

import time
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

TOKEN_SERVICE = "google_calendar"
TOKEN_EXPIRY_MARGIN_SECONDS = 60


def _save_calendar_token(
    token_data: dict[str, Any],
    *,
    previous_refresh_token: str | None = None,
) -> None:
    """Sauvegarde le token Calendar avec une date d'expiration exploitable."""
    payload = dict(token_data)

    refresh_token = payload.get("refresh_token") or previous_refresh_token
    if refresh_token:
        payload["refresh_token"] = str(refresh_token)

    expires_in = int(payload.get("expires_in", 3600))
    payload["expires_at"] = time.time() + expires_in - TOKEN_EXPIRY_MARGIN_SECONDS

    save_token_json(TOKEN_SERVICE, payload)


def _refresh_access_token(tokens: dict[str, Any]) -> str:
    """Obtient un nouvel access token à partir du refresh token."""
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise ValueError(
            "Le token Calendar a expiré et aucun refresh_token n'est disponible. "
            "Une nouvelle connexion Google est nécessaire."
        )

    response = httpx.post(
        GOOGLE_TOKEN_URL,
        data={
            "client_id": settings.google_calendar_client_id,
            "client_secret": settings.google_calendar_client_secret,
            "refresh_token": str(refresh_token),
            "grant_type": "refresh_token",
        },
        timeout=15,
    )

    if response.status_code == 200:
        refreshed = response.json()

        if not isinstance(refreshed, dict) or not refreshed.get("access_token"):
            raise RuntimeError("Google n'a pas renvoyé de nouvel access_token Calendar.")

        _save_calendar_token(
            refreshed,
            previous_refresh_token=str(refresh_token),
        )
        return str(refreshed["access_token"])

    if response.status_code == 400 and "invalid_grant" in response.text:
        raise ValueError(
            "L'autorisation Google Calendar a été révoquée ou a expiré. "
            "Une nouvelle connexion est nécessaire."
        )

    raise RuntimeError(
        f"Échec du renouvellement Calendar : " f"{response.status_code} {response.text}"
    )


def _get_access_token(*, force_refresh: bool = False) -> str:
    """Retourne un access token valide, renouvelé automatiquement si nécessaire."""
    tokens = load_token_json(TOKEN_SERVICE)
    access_token = tokens.get("access_token")
    refresh_token = tokens.get("refresh_token")
    expires_at = tokens.get("expires_at")

    if force_refresh:
        return _refresh_access_token(tokens)

    if not access_token:
        if refresh_token:
            return _refresh_access_token(tokens)

        raise ValueError("Calendar non connecté : aucun access_token trouvé")

    # Les anciens fichiers de token n'ont pas encore expires_at.
    # Si un refresh_token existe, on renouvelle une fois afin de normaliser le fichier.
    if expires_at is None and refresh_token:
        return _refresh_access_token(tokens)

    if expires_at is not None:
        try:
            expired = float(expires_at) <= time.time()
        except (TypeError, ValueError):
            expired = True

        if expired:
            return _refresh_access_token(tokens)

    return str(access_token)


def _authorization_headers(*, force_refresh: bool = False) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {_get_access_token(force_refresh=force_refresh)}",
        "Accept": "application/json",
    }


def _authorized_get(
    url: str,
    *,
    params: dict[str, str | int] | None = None,
) -> httpx.Response:
    """Exécute un GET Google et retente une fois après un renouvellement sur 401."""
    response = httpx.get(
        url,
        headers=_authorization_headers(),
        params=params,
        timeout=15,
    )

    if response.status_code != 401:
        return response

    response = httpx.get(
        url,
        headers=_authorization_headers(force_refresh=True),
        params=params,
        timeout=15,
    )

    if response.status_code == 401:
        raise ValueError(
            "Google Calendar refuse le token renouvelé. " "Une nouvelle connexion est nécessaire."
        )

    return response


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
        token_data = response.json()

        if not isinstance(token_data, dict):
            raise RuntimeError("Réponse OAuth Calendar invalide.")

        _save_calendar_token(token_data)
        return True

    if response.status_code == 400:
        raise ValueError(f"Code OAuth expiré ou invalide : {response.text}")

    raise RuntimeError(f"Erreur OAuth Calendar : {response.status_code} {response.text}")


def get_calendars() -> list[dict[str, Any]]:
    response = _authorized_get(CALENDAR_LIST_URL)
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

    response = _authorized_get(
        CALENDAR_EVENTS_URL,
        params=params,
    )
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
