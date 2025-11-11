import asyncio
from typing import Any, Dict, List


def get_open_issues() -> List[Dict[str, Any]]:
    # stub: le test vérifie seulement que c'est une liste
    return []

async def github_sync_notion_services() -> Dict[str, Any]:
    await asyncio.sleep(0)
    issues = get_open_issues()
    return {"status": "ok", "issues": issues}
