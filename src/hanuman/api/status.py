import logging
from typing import Any, Dict

from fastapi import APIRouter

from hanuman.core.config import get_env_var  # 🔁 Nouvelle importation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
def get_status() -> Dict[str, Any]:
    logger.info("✅ Endpoint /status appelé")

    response = {"status": "ok", "version": "0.2.0"}

    # Si on est en DEBUG (défini dans .env), on affiche une preview du token
    if get_env_var("DEBUG", "false") == "true":
        token_preview = get_env_var("NOTION_TOKEN", "")
        if token_preview:
            response["notion_token_preview"] = token_preview[:6] + "..."

    return response
