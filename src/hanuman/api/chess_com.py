# src/hanuman/api/chess_com.py

from fastapi import APIRouter, Request
from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.services.chess_service import ping_chess

router = APIRouter()
logger = get_logger("chess")


@router.get("/chess/ping", response_model=PingResult)
def chess_ping(request: Request) -> PingResult:
    client_ip = request.client.host
    logger.bind(ip=client_ip, endpoint="/chess/ping").info("📨 Appel API /chess/ping")
    return ping_chess()
