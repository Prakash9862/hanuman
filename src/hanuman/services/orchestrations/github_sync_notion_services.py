from typing import Any, Dict
from hanuman.orchestrations.github_sync_notion import sync_github_to_notion as _sync

async def github_sync_notion_services() -> Dict[str, Any]:
    # Legacy async wrapper for tests; call sync orchestration.
    return _sync()
