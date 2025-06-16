# src/hanuman/api/github.py

from fastapi import APIRouter, Request
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.github_service import ping_github

router = APIRouter()
logger = get_logger("github")


@router.get("/github/ping", response_model=PingResult)
def github_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/github/ping").info("📨 Appel API /github/ping")
    return ping_github()
