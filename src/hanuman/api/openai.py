# src/hanuman/api/openai.py

from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.openai_service import ping_openai
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/openai/ping", response_model=PingResult)
@trace_endpoint("openai", catch=True)
def openai_ping(request: Request) -> PingResult:
    return ping_openai()
