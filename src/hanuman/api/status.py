from typing import Dict, Optional

from fastapi import APIRouter, Request

from hanuman.core.config import get_env_var
from hanuman.core.token_manager import TOKEN_DIR, load_token_json
from hanuman.models.status import StatusResult
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/status", response_model=StatusResult)
@trace_endpoint("status", catch=True)
def get_status(request: Request) -> StatusResult:
    debug_mode = get_env_var("DEBUG", "false")

    status = "ok"
    version = "0.2.0"
    token_previews: Optional[Dict[str, str]] = None

    if debug_mode == "true":
        previews: Dict[str, str] = {}
        for token_file in TOKEN_DIR.glob("*_token.json"):
            service = token_file.stem.replace("_token", "")
            token_data = load_token_json(service)
            token_value = token_data.get("token") or token_data.get("access_token")
            if token_value:
                previews[service] = token_value[:6] + "..."

        if previews:
            token_previews = previews

    return StatusResult(
        status=status,
        version=version,
        token_previews=token_previews,
    )
