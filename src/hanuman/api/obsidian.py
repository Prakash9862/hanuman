# src/hanuman/api/obsidian.py

from fastapi import APIRouter, Request
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.obsidian_service import ping_obsidian

router = APIRouter()
logger = get_logger("obsidian")


@router.get("/obsidian/ping", response_model=PingResult)
def obsidian_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/obsidian/ping").info("📨 Appel API /obsidian/ping")
    return ping_obsidian()
