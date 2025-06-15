# src/hanuman/api/chess_com.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Ajout typage strict
from hanuman.services.chess_service import ping_chess

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/chess/ping", response_model=PingResult)
def chess_ping() -> PingResult:
    logger.info("📨 Appel API /chess/ping")
    return ping_chess()
