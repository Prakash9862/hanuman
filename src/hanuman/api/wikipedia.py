# src/hanuman/api/wikipedia.py

from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.wikipedia_service import ping_wikipedia
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/wikipedia/ping", response_model=PingResult)
@trace_endpoint("wikipedia", catch=True)
def wikipedia_ping(request: Request) -> PingResult:
    return ping_wikipedia()
