from __future__ import annotations

from datetime import UTC, datetime
from urllib.parse import urlencode

from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from hanuman.core.config import settings
from hanuman.services.core.calendar_service import (
    exchange_code_for_token,
    get_calendars,
    get_upcoming_events,
)
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/calendar/auth")
@trace_endpoint("calendar", catch=False)
def calendar_auth(request: Request) -> RedirectResponse:
    params = {
        "client_id": settings.google_calendar_client_id,
        "redirect_uri": settings.google_calendar_redirect_uri,
        "response_type": "code",
        "scope": "https://www.googleapis.com/auth/calendar.readonly",
        "access_type": "offline",
        "prompt": "consent",
    }

    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth?"
        + urlencode(params)
    )

    return RedirectResponse(auth_url)


@router.get("/calendar/callback")
@trace_endpoint("calendar", catch=False)
def calendar_callback(request: Request) -> JSONResponse:
    code = request.query_params.get("code")
    error = request.query_params.get("error")

    if error:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": error},
        )

    if not code:
        return JSONResponse(
            status_code=400,
            content={"ok": False, "error": "Missing code"},
        )

    success = exchange_code_for_token(code)

    if success:
        return JSONResponse(
            {
                "ok": True,
                "message": "Google Calendar est connecté à Hanuman.",
            }
        )

    return JSONResponse(
        status_code=500,
        content={
            "ok": False,
            "error": "Échec de l’échange du code OAuth",
        },
    )


@router.get("/calendar/status")
@trace_endpoint("calendar", catch=True)
def calendar_status(request: Request) -> dict:
    calendars = get_calendars()

    return {
        "ok": True,
        "connected": True,
        "calendar_count": len(calendars),
    }


@router.get("/calendar/calendars")
@trace_endpoint("calendar", catch=True)
def calendar_list(request: Request) -> dict:
    calendars = get_calendars()

    return {
        "ok": True,
        "count": len(calendars),
        "calendars": calendars,
    }


@router.get("/calendar/events")
@trace_endpoint("calendar", catch=True)
def calendar_events(
    request: Request,
    max_results: int = Query(default=20, ge=1, le=100),
) -> dict:
    events = get_upcoming_events(max_results=max_results)

    return {
        "ok": True,
        "count": len(events),
        "events": events,
    }


@router.get("/calendar/ping")
@trace_endpoint("calendar", catch=True)
def calendar_ping(request: Request) -> dict:
    calendars = get_calendars()

    return {
        "ok": True,
        "source": "calendar",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {
            "calendar_count": len(calendars),
        },
    }