# src/hanuman/api/github.py

from fastapi import APIRouter, Request

from hanuman.models.ping import PingResult
from hanuman.services.github_service import ping_github
from hanuman.utils.decorators import trace_endpoint

router = APIRouter()


@router.get("/github/ping", response_model=PingResult)
@trace_endpoint("github", catch=True)
def github_ping(request: Request) -> PingResult:
    return ping_github()
