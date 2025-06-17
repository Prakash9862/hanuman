# src/hanuman/api/status.py

from fastapi import APIRouter, Request

from hanuman.core.config import get_env_var
from hanuman.core.token_manager import load_token_json
from hanuman.models.status import StatusResult
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/status", response_model=StatusResult)
@trace_endpoint("status", catch=True)
def get_status(request: Request) -> StatusResult:
    debug_mode = get_env_var("DEBUG", "false")

    data = {
        "status": "ok",
        "version": "0.2.0",
    }

    if debug_mode == "true":
        token_data = load_token_json("notion")
        token_value = token_data.get("token") or token_data.get("access_token")
        if token_value:
            data["notion_token_preview"] = token_value[:6] + "..."

    return StatusResult(**data)
