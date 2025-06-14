# src/hanuman/api/notion.py

import logging

from fastapi import APIRouter
from hanuman.services.notion_service import ping_notion

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/notion/ping")
def notion_ping():
    logger.info("📨 Appel API /notion/ping")
    return ping_notion()
