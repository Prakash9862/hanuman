from typing import Any, Dict

from . import github_sync_notion_services as github_sync_notion_services  # module


# optionnel pendant la migration
def sync_github_to_notion() -> Dict[str, Any]:
    return {"status": "stub"}

__all__ = ["github_sync_notion_services", "sync_github_to_notion"]
