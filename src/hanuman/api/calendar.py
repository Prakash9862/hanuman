# src/hanuman/api/calendar.py

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from hanuman.core.config import get_env_var
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.calendar_service import exchange_code_for_token

router = APIRouter()
logger = get_logger("calendar")


@router.get("/calendar/auth")
def calendar_auth(request: Request) -> RedirectResponse:
    client_ip = request.client.host
    logger.bind(ip=client_ip).info("🔐 Démarrage auth Google Calendar")

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
def calendar_callback(request: Request) -> JSONResponse:
    client_ip = request.client.host
    code = request.query_params.get("code")

    log = logger.bind(ip=client_ip, endpoint="/calendar/callback")

    if not code:
        log.error("❌ Aucun code OAuth2 reçu")
        return JSONResponse({"ok": False, "error": "Missing code"})

    log.info("🔁 Code OAuth2 reçu, échange en cours…")
    success = exchange_code_for_token(code)

    if success:
        return JSONResponse({"ok": True, "message": "Token reçu et stocké 🎉"})
    else:
        return JSONResponse({"ok": False, "error": "Échec de l’échange de code"})


@router.get("/calendar/ping", response_model=PingResult)
def calendar_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/calendar/ping").info("📨 Appel API /calendar/ping")
    return PingResult(ok=True, source="calendar")
