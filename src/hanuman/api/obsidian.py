# src/hanuman/api/obsidian.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Typage modèle global
from hanuman.services.obsidian_service import ping_obsidian

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/obsidian/ping", response_model=PingResult)
def obsidian_ping() -> PingResult:
    logger.info("📨 Appel API /obsidian/ping")
    return ping_obsidian()
