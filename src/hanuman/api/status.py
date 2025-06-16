from fastapi import APIRouter, Request
from hanuman.core.config import get_env_var
from hanuman.core.logging import get_logger
from hanuman.models.status import StatusResult

router = APIRouter()
logger = get_logger("status")


@router.get("/status", response_model=StatusResult)
def get_status(request: Request) -> StatusResult:
    client_ip = request.client.host
    debug_mode = get_env_var("DEBUG", "false")

    logger.bind(endpoint="/status", ip=client_ip, debug_mode=debug_mode).info(
        "✅ Endpoint /status appelé"
    )

    data = {
        "status": "ok",
        "version": "0.2.0",
    }

    if debug_mode == "true":
        token_preview = get_env_var("NOTION_TOKEN", "")
        if token_preview:
            data["notion_token_preview"] = token_preview[:6] + "..."

    return StatusResult(**data)
