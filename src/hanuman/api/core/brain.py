from __future__ import annotations

from fastapi import APIRouter, Query

from hanuman.services.core.github_service import GithubService
from hanuman.services.core.system_service import get_system_status

router = APIRouter()


@router.get("/brain/system")
def brain_system() -> dict:
    return {"ok": True, "system": get_system_status()}


@router.get("/brain/github")
def brain_github(
    include_repos: bool = Query(True, description="Inclut la liste des repos"),
    repos_limit: int = Query(50, ge=1, le=100),
    include_issues: bool = Query(False, description="Inclut les issues par repo"),
    issues_limit: int = Query(10, ge=1, le=100),
) -> dict:
    service = GithubService()
    user = service.get_user()
    response: dict = {"ok": True, "user": user}

    if include_repos:
        repos = service.list_repos(limit=repos_limit)
        response["repos"] = [repo.__dict__ for repo in repos]

        if include_issues:
            issues_by_repo = {}
            for repo in repos:
                issues_by_repo[repo.full_name] = service.list_issues(
                    full_name=repo.full_name,
                    limit=issues_limit,
                )
            response["issues"] = issues_by_repo

    return response


@router.get("/brain/overview")
def brain_overview(
    include_repos: bool = Query(True, description="Inclut la liste des repos"),
    repos_limit: int = Query(50, ge=1, le=100),
) -> dict:
    service = GithubService()
    user = service.get_user()
    repos = service.list_repos(limit=repos_limit) if include_repos else []

    return {
        "ok": True,
        "system": get_system_status(),
        "github": {
            "user": user,
            "repos": [repo.__dict__ for repo in repos],
        },
    }
