# src/hanuman/api/github.py

import logging

from fastapi import APIRouter

from hanuman.services.github_service import ping_github

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/github/ping")
def github_ping():
    logger.info("📨 Appel API /github/ping")
    return ping_github()
