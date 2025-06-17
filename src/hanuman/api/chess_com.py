# src/hanuman/api/chess_com.py

from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.chess_service import ping_chess
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/chess/ping", response_model=PingResult)
@trace_endpoint("chess", catch=True)
def chess_ping(request: Request) -> PingResult:
    return ping_chess()
