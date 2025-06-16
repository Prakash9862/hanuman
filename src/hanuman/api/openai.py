# src/hanuman/api/openai.py

from fastapi import APIRouter, Request
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.openai_service import ping_openai

router = APIRouter()
logger = get_logger("openai")


@router.get("/openai/ping", response_model=PingResult)
def openai_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/openai/ping").info("📨 Appel API /openai/ping")
    return ping_openai()
