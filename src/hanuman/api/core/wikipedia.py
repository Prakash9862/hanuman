# src/hanuman/api/wikipedia.py

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/wikipedia/ping")
def wikipedia_ping() -> dict:
    return {
        "ok": True,
        "source": "wikipedia",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {"title": "wikipedia"},
    }
