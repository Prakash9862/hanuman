# src/hanuman/api/wikipedia.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Typage global
from hanuman.services.wikipedia_service import ping_wikipedia

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/wikipedia/ping", response_model=PingResult)
def wikipedia_ping() -> PingResult:
    logger.info("📨 Appel API /wikipedia/ping")
    return ping_wikipedia()
