# src/hanuman/api/notion.py

from fastapi import APIRouter, Request
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.notion_service import ping_notion

router = APIRouter()
logger = get_logger("notion")


@router.get("/notion/ping", response_model=PingResult)
def notion_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/notion/ping").info("📨 Appel API /notion/ping")
    return ping_notion()
