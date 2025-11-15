# src/hanuman/api/chess_com.py

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/chess/ping")
def chess_ping() -> dict:
    return {
        "ok": True,
        "source": "chess",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {
            "username": "prakasch",
        },
    }
