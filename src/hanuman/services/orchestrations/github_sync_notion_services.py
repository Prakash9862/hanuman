from __future__ import annotations

from typing import Any, Dict, TypedDict


class SyncResult(TypedDict, total=False):
    repo: str
    page: str
    synced: int
    status: str
    detail: str


def sync_github_to_notion(repo: str, notion_page_id: str) -> Dict[str, Any]:
    """
    Shim minimal (post-refactor) pour garder une API stable côté services.
    À remplacer ensuite par l'implémentation réelle (appel GitHub + Notion).
    """
    result: Dict[str, Any] = {
        "repo": repo,
        "page": notion_page_id,
        "synced": 0,
        "status": "noop",
        "detail": "orchestration stubbed after refactor",
    }
    return result
