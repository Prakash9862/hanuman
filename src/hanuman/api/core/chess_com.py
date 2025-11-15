# src/hanuman/api/chess_com.py

from fastapi import APIRouter, Request
from datetime import datetime, UTC


from hanuman.models.ping import PingResult
from hanuman.services.core.chess_service import ping_chess
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/chess/ping")
def chess_ping() -> dict:
    return {
        "ok": True,
        "source": "chess",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {},
    }
