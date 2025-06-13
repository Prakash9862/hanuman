# src/hanuman/api/status.py

from fastapi import APIRouter
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/status")
def get_status():
    logger.info("✅ Endpoint /status appelé")
    return {"status": "ok", "version": "0.1.0"}
