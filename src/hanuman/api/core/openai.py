# src/hanuman/api/openai.py

from datetime import UTC, datetime

from fastapi import APIRouter

router = APIRouter()


@router.get("/openai/ping")
def openai_ping() -> dict:
    # Tu pourras plus tard compter vraiment les modèles configurés,
    # mais pour le test, un entier suffit.
    return {
        "ok": True,
        "source": "openai",
        "status": 200,
        "timestamp": datetime.now(UTC).isoformat(),
        "detail": {
            "model_count": 1,
        },
    }
