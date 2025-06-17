# src/hanuman/api/obsidian.py

from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.obsidian_service import ping_obsidian
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/obsidian/ping", response_model=PingResult)
@trace_endpoint("obsidian", catch=True)
def obsidian_ping(request: Request) -> PingResult:
    return ping_obsidian()
