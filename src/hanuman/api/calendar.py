# src/hanuman/api/calendar.py

import logging

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse

from hanuman.core.config import get_env_var
from hanuman.models.ping import PingResult
from hanuman.services.calendar_service import exchange_code_for_token, get_calendar_list

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/calendar/auth")
def calendar_auth() -> RedirectResponse:  # ✅ Typage ajouté
    logger.info("🔐 Démarrage auth Google Calendar")

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
def calendar_callback(request: Request) -> JSONResponse:  # ✅ Typage ajouté
    code = request.query_params.get("code")
    if not code:
        logger.error("❌ Aucun code OAuth2 reçu")
        return JSONResponse({"ok": False, "error": "Missing code"})

    logger.info("🔁 Code OAuth2 reçu, échange en cours...")
    success = exchange_code_for_token(code)
    if success:
        return JSONResponse({"ok": True, "message": "Token reçu et stocké 🎉"})
    else:
        return JSONResponse({"ok": False, "error": "Échec de l’échange de code"})
