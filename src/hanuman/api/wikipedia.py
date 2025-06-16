# src/hanuman/api/wikipedia.py

from fastapi import APIRouter, Request

from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.wikipedia_service import ping_wikipedia

router = APIRouter()
logger = get_logger("wikipedia")


@router.get("/wikipedia/ping", response_model=PingResult)
def wikipedia_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/wikipedia/ping").info("📨 Appel API /wikipedia/ping")
    return ping_wikipedia()
