from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter

from hanuman.services.core.github_service import (
    GithubApiError,
    GithubAuthError,
    GithubService,
)
from hanuman.services.core.system_state_service import get_system_state

router = APIRouter(prefix="/brain", tags=["brain"])


def _compact_user(user: dict) -> dict:
    return {
        "login": user.get("login"),
        "name": user.get("name"),
        "html_url": user.get("html_url"),
        "public_repos": user.get("public_repos"),
        "followers": user.get("followers"),
        "following": user.get("following"),
    }


@router.get("/snapshot")
def brain_snapshot(
    repo: str | None = None,
    state: str = "open",
    limit: int = 25,
    include_repos: bool = False,
) -> dict:
    """Snapshot combiné GitHub + état système."""
    safe_limit = max(1, min(limit, 100))
    system_state = get_system_state()

    github_payload: dict = {}
    github_ok = False
    try:
        github = GithubService()
        user = github.get_user()
        github_payload["user"] = _compact_user(user)
        github_payload["repo"] = github.get_repo(repo).__dict__
        github_payload["issues"] = github.list_issues(
            full_name=repo,
            state=state,
            limit=safe_limit,
        )
        if include_repos:
            github_payload["repos"] = github.list_repos(limit=safe_limit)
        github_ok = True
    except (GithubAuthError, GithubApiError, ValueError) as exc:
        github_payload["error"] = str(exc)

    return {
        "ok": github_ok,
        "timestamp": datetime.now(UTC).isoformat(),
        "github": github_payload,
        "system": system_state,
    }
