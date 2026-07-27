from __future__ import annotations

from typing import Any

import pytest

from hanuman.services.core.github_service import (
    GithubApiError,
    GithubAuthError,
    GithubRepo,
    GithubService,
)


class FakeGithubService(GithubService):
    """
    Version fake qui évite tout appel réseau et ne dépend pas du token réel.
    On override __init__ pour ne pas déclencher la logique d'auth.
    """

    def __init__(self) -> None:  # type: ignore[override]
        # pas de super().__init__, on ne veut pas toucher à l'env
        self._token = "dummy"
        self._headers = {}

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:  # type: ignore[override]
        # Simule le comportement minimal pour get_user / get_repo / list_issues
        if path == "/user":
            return {"login": "demo-user"}

        if path.startswith("/repos/") and path.endswith("/issues"):
            # mélange d'issue normale et de PR (à filtrer)
            return [
                {
                    "id": 1,
                    "number": 1,
                    "title": "Bug: something is wrong",
                    "state": "open",
                    "html_url": "https://github.com/owner/repo/issues/1",
                    "labels": [{"name": "bug"}, {"name": "urgent"}],
                },
                {
                    "id": 2,
                    "number": 2,
                    "title": "Feature: add something",
                    "state": "open",
                    "html_url": "https://github.com/owner/repo/pull/2",
                    "labels": [{"name": "feature"}],
                    "pull_request": {"url": "https://api.github.com/..."},
                },
            ]

        if path.startswith("/repos/") and path.endswith("/commits"):
            return [
                {
                    "sha": "2" * 40,
                    "parents": [{"sha": "1" * 40}],
                    "author": {"login": "demo-user"},
                    "commit": {
                        "author": {
                            "name": "Demo User",
                            "email": "private@example.test",
                            "date": "2026-07-27T10:00:00Z",
                        },
                        "committer": {"date": "2026-07-27T10:01:00Z"},
                        "message": "Second commit\n\nBody",
                    },
                    "html_url": f"https://github.com/Owner/repo/commit/{'2' * 40}",
                },
                {
                    "sha": "1" * 40,
                    "parents": [],
                    "author": {"login": "demo-user"},
                    "commit": {
                        "author": {
                            "name": "Demo User",
                            "date": "2026-07-27T09:00:00Z",
                        },
                        "committer": {"date": "2026-07-27T09:01:00Z"},
                        "message": "First commit",
                    },
                    "html_url": f"https://github.com/Owner/repo/commit/{'1' * 40}",
                },
            ]

        if path.startswith("/repos/") and "issues" not in path and "commits" not in path:
            return {
                "id": 123,
                "owner": {"login": "Owner"},
                "name": "repo",
                "full_name": "Owner/repo",
                "description": "Demo repo",
                "stargazers_count": 42,
                "forks_count": 3,
                "html_url": "https://github.com/Owner/repo",
                "default_branch": "main",
            }

        raise GithubApiError(f"Path inattendu dans FakeGithubService: {path}")


def test_github_service_get_user() -> None:
    service = FakeGithubService()
    user = service.get_user()
    assert user["login"] == "demo-user"


def test_github_service_get_repo_maps_fields() -> None:
    service = FakeGithubService()
    repo = service.get_repo("Owner/repo")
    assert isinstance(repo, GithubRepo)
    assert repo.repository_id == 123
    assert repo.owner == "Owner"
    assert repo.name == "repo"
    assert repo.full_name == "Owner/repo"
    assert repo.description == "Demo repo"
    assert repo.stars == 42
    assert repo.forks == 3
    assert repo.html_url == "https://github.com/Owner/repo"
    assert repo.default_branch == "main"


def test_github_service_list_issues_filters_pull_requests() -> None:
    service = FakeGithubService()
    issues = service.list_issues("Owner/repo", state="open", limit=50)

    # On doit garder uniquement l'issue, pas la PR
    assert len(issues) == 1
    issue = issues[0]

    assert issue["id"] == 1
    assert issue["number"] == 1
    assert issue["title"].startswith("Bug:")
    assert issue["state"] == "open"
    assert issue["url"].endswith("/issues/1")
    assert issue["labels"] == ["bug", "urgent"]


def test_github_service_lists_bounded_commits_oldest_first() -> None:
    service = FakeGithubService()
    commits = service.list_commits("Owner/repo", ref="main", max_commits=2)

    assert [commit.sha for commit in commits] == ["1" * 40, "2" * 40]
    assert commits[1].parent_shas == ("1" * 40,)
    assert commits[1].github_author == "demo-user"
    assert commits[1].git_author == "Demo User"
    assert "private@example.test" not in repr(commits)


def test_github_service_start_sha_is_exclusive() -> None:
    service = FakeGithubService()
    commits = service.list_commits(
        "Owner/repo",
        ref="main",
        start_sha="1" * 40,
        max_commits=2,
    )
    assert [commit.sha for commit in commits] == ["2" * 40]


def test_github_service_rejects_missing_start_bound() -> None:
    service = FakeGithubService()
    with pytest.raises(GithubApiError, match="borne de départ"):
        service.list_commits(
            "Owner/repo",
            ref="main",
            start_sha="f" * 40,
            max_commits=2,
        )


def test_github_service_init_raises_without_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # On patch directement la constante GITHUB_TOKEN du module,
    # car elle est déjà évaluée à l'import.
    from hanuman.services.core import github_service as github_module

    monkeypatch.setattr(github_module, "GITHUB_TOKEN", "")

    # Sans token explicite ET avec GITHUB_TOKEN vidé, le service doit refuser de démarrer
    with pytest.raises(GithubAuthError):
        GithubService(token=None)
