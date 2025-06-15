# src/hanuman/api/github.py

import logging

from fastapi import APIRouter

from hanuman.models.ping import PingResult  # ✅ Typage ajouté
from hanuman.services.github_service import ping_github

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/github/ping", response_model=PingResult)
def github_ping() -> PingResult:
    logger.info("📨 Appel API /github/ping")
    return ping_github()
