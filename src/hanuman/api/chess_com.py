# src/hanuman/api/chess_com.py

import logging

from fastapi import APIRouter

from hanuman.services.chess_service import ping_chess

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/chess/ping")
def chess_ping():
    logger.info("📨 Appel API /chess/ping")
    return ping_chess()
