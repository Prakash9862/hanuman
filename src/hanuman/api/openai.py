# src/hanuman/api/openai.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Import modèle typé
from hanuman.services.openai_service import ping_openai

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/openai/ping", response_model=PingResult)
def openai_ping() -> PingResult:
    logger.info("📨 Appel API /openai/ping")
    return ping_openai()
