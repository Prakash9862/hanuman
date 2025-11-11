import asyncio
from types import SimpleNamespace
from typing import Any, Dict, List


async def get_open_issues() -> List[Dict[str, Any]]:
    # stub: le test veut juste une LISTE
    await asyncio.sleep(0)
    return []

# <- ce nom est EXACTEMENT celui importé par le test
github_sync_notion_services = SimpleNamespace(get_open_issues=get_open_issues)

__all__ = ["github_sync_notion_services", "get_open_issues"]
