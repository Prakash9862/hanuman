# src/hanuman/api/obsidian.py

import logging

from fastapi import APIRouter

from hanuman.services.obsidian_service import ping_obsidian

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/obsidian/ping")
def obsidian_ping():
    logger.info("📨 Appel API /obsidian/ping")
    return ping_obsidian()
