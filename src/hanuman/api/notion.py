# src/hanuman/api/notion.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Typage modèle global
from hanuman.services.notion_service import ping_notion

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/notion/ping", response_model=PingResult)
def notion_ping() -> PingResult:
    logger.info("📨 Appel API /notion/ping")
    return ping_notion()
