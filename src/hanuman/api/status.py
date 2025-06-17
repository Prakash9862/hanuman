# src/hanuman/api/status.py

from fastapi import APIRouter, Request

from hanuman.core.config import get_env_var
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
        token_preview = get_env_var("NOTION_TOKEN", "")
        if token_preview:
            data["notion_token_preview"] = token_preview[:6] + "..."

    return StatusResult(**data)
