# src/hanuman/api/github.py

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/github/ping")
def github_ping() -> dict:
    return {
        "ok": True,
        "source": "github",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {
            "login": "prakasch",
        },
    }
