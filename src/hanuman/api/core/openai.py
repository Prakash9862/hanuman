# src/hanuman/api/openai.py

from fastapi import APIRouter, Request
from datetime import datetime, UTC


from hanuman.models.ping import PingResult
from hanuman.services.core.openai_service import ping_openai
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/openai/ping")
def openai_ping() -> dict:
    return {
        "ok": True,
        "source": "openai",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {},
    }
