# src/hanuman/api/github_sync_notion.py

from typing import Any, Dict

from fastapi import APIRouter

from hanuman.services.orchestrations.github_sync_notion_services import (
    sync_issues_to_notion,
)

router = APIRouter()


@router.post("/github_sync_notion/sync")
async def sync_github_dashboard() -> Dict[str, Any]:
    return await sync_issues_to_notion()
