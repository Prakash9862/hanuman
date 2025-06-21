from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.core.notion_service import ping_notion
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/notion/ping", response_model=PingResult)
@trace_endpoint("notion", catch=True)
def notion_ping(request: Request) -> PingResult:
    return ping_notion()
