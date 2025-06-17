# src/hanuman/api/calendar.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from hanuman.core.config import get_env_var
from hanuman.models.ping import PingResult
from hanuman.services.calendar_service import exchange_code_for_token
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/calendar/auth")
@trace_endpoint("calendar", catch=False)
def calendar_auth(request: Request) -> RedirectResponse:

    client_id = get_env_var("GOOGLE_CLIENT_ID")
    redirect_uri = get_env_var("GOOGLE_REDIRECT_URI")

    scope = "https://www.googleapis.com/auth/calendar.readonly"
    auth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={client_id}"
        f"&redirect_uri={redirect_uri}"
        f"&response_type=code"
        f"&scope={scope}"
        f"&access_type=offline"
        f"&prompt=consent"
    )
    return RedirectResponse(auth_url)


@router.get("/calendar/callback")
@trace_endpoint("calendar", catch=False)
def calendar_callback(request: Request) -> JSONResponse:
    code = request.query_params.get("code")

    if not code:
        return JSONResponse({"ok": False, "error": "Missing code"})

    success = exchange_code_for_token(code)

    if success:
        return JSONResponse({"ok": True, "message": "Token reçu et stocké 🎉"})
    else:
        return JSONResponse({"ok": False, "error": "Échec de l’échange de code"})


@router.get("/calendar/ping", response_model=PingResult)
@trace_endpoint("calendar", catch=True)
def calendar_ping(request: Request) -> PingResult:
    return PingResult(ok=True, source="calendar")
