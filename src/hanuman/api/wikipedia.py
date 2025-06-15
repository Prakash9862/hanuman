# src/hanuman/api/wikipedia.py

import logging

from fastapi import APIRouter

from hanuman.services.wikipedia_service import ping_wikipedia

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/wikipedia/ping")
def wikipedia_ping():
    logger.info("📨 Appel API /wikipedia/ping")
    return ping_wikipedia()
