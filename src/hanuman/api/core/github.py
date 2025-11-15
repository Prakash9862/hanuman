# src/hanuman/api/github.py

from fastapi import APIRouter, Request
from datetime import datetime, UTC


from hanuman.models.ping import PingResult
from hanuman.services.core.github_service import ping_github
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/github/ping")
def github_ping() -> dict:
    return {
        "ok": True,
        "source": "github",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {},
    }
