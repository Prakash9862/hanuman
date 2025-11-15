# src/hanuman/api/wikipedia.py

from fastapi import APIRouter, Request
from datetime import datetime, UTC


from hanuman.models.ping import PingResult
from hanuman.services.core.wikipedia_service import ping_wikipedia
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/wikipedia/ping")
def wikipedia_ping() -> dict:
    return {
        "ok": True,
        "source": "wikipedia",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {},
    }
