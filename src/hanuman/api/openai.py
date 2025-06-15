# src/hanuman/api/openai.py

import logging

from fastapi import APIRouter

from hanuman.services.openai_service import ping_openai

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/openai/ping")
def openai_ping():
    logger.info("📨 Appel API /openai/ping")
    return ping_openai()
