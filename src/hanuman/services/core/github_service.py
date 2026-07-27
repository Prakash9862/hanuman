from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, cast

import httpx

from hanuman.config.env import GITHUB_REPO, GITHUB_TOKEN
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

GITHUB_API_BASE_URL = "https://api.github.com"


class GithubAuthError(RuntimeError):
    """Erreur d'authentification GitHub (token manquant ou invalide)."""


class GithubApiError(RuntimeError):
    """Erreur générique lors d'un appel à l'API GitHub."""


@dataclass
class GithubRepo:
    repository_id: int
    owner: str
    name: str
    full_name: str
    description: str
    stars: int
    forks: int
    html_url: str
    default_branch: str


@dataclass(frozen=True)
class GithubCommit:
    sha: str
    parent_shas: tuple[str, ...]
    authored_at: str
    committed_at: str
    git_author: str
    github_author: str | None
    message: str
    html_url: str


class GithubService:
    """Client GitHub centralisé pour Hanuman.

    - Utilise le token défini dans hanuman.config.env
    - Fournit des méthodes simples : get_user, get_repo, list_issues
    - Tous les appels passent par httpx avec un timeout raisonnable.
    """

    def __init__(self, token: Optional[str] = None) -> None:
        self._token = (token or GITHUB_TOKEN or "").strip()
        if not self._token:
            raise GithubAuthError(
                "GITHUB_TOKEN manquant. Configure-le dans le .env ou passe-le au constructeur."
            )

        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github+json",
        }

    # ------------------------------------------------------------------ #
    #  Méthode interne basse-niveau
    # ------------------------------------------------------------------ #

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Appel bas niveau à l'API GitHub.

        Retourne le JSON décodé (dict ou list selon l'endpoint).
        """
        url = f"{GITHUB_API_BASE_URL.rstrip('/')}/{path.lstrip('/')}"
        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=self._headers,
                timeout=10.0,
                **kwargs,
            )
        except httpx.RequestError as exc:
            raise GithubApiError(f"Erreur réseau vers GitHub: {exc}") from exc

        if response.status_code == 401:
            raise GithubAuthError("Token GitHub invalide ou expiré.")

        if response.status_code >= 400:
            raise GithubApiError(f"Erreur GitHub {response.status_code}: {response.text}")

        return response.json()

    # ------------------------------------------------------------------ #
    #  Méthodes publiques
    # ------------------------------------------------------------------ #

    def get_user(self) -> Dict[str, Any]:
        """Retourne les infos du user GitHub lié au token."""
        data = self._request("GET", "/user")
        return cast(Dict[str, Any], data)

    def get_repo(self, full_name: Optional[str] = None) -> GithubRepo:
        """Retourne les infos d'un repo (ex: 'Prakash9862/hanuman')."""
        repo_name = (full_name or GITHUB_REPO or "").strip()
        if not repo_name:
            raise ValueError(
                "Aucun repo spécifié. Passe full_name ou configure GITHUB_REPO dans le .env."
            )

        data = self._request("GET", f"/repos/{repo_name}")
        repo = cast(Dict[str, Any], data)

        return GithubRepo(
            repository_id=int(repo.get("id", 0)),
            owner=str(repo.get("owner", {}).get("login", "")),
            name=str(repo.get("name", "")),
            full_name=repo.get("full_name", repo_name),
            description=repo.get("description") or "",
            stars=int(repo.get("stargazers_count", 0)),
            forks=int(repo.get("forks_count", 0)),
            html_url=repo.get("html_url", ""),
            default_branch=repo.get("default_branch", "main"),
        )

    def list_commits(
        self,
        full_name: str,
        *,
        ref: str,
        start_sha: str | None = None,
        max_commits: int = 50,
    ) -> List[GithubCommit]:
        """Retourne une plage bornée de commits, du plus ancien au plus récent.

        ``start_sha`` est une borne exclusive. GitHub renvoie les commits du
        plus récent au plus ancien ; la méthode inverse le résultat après avoir
        vérifié que la borne demandée a été rencontrée.
        """

        if not full_name.strip():
            raise ValueError("Le dépôt GitHub est obligatoire.")
        if not ref.strip():
            raise ValueError("La branche ou ref GitHub est obligatoire.")
        if max_commits < 1 or max_commits > 100:
            raise ValueError("max_commits doit être compris entre 1 et 100.")

        params: Dict[str, Any] = {"sha": ref, "per_page": max_commits}
        data = self._request("GET", f"/repos/{full_name}/commits", params=params)
        raw_commits = cast(List[Dict[str, Any]], data)
        commits: List[GithubCommit] = []
        found_start = start_sha is None

        for raw in raw_commits:
            sha = str(raw.get("sha", "")).strip()
            if start_sha is not None and sha == start_sha:
                found_start = True
                break

            commit_data = cast(Dict[str, Any], raw.get("commit") or {})
            author_data = cast(Dict[str, Any], commit_data.get("author") or {})
            committer_data = cast(Dict[str, Any], commit_data.get("committer") or {})
            github_author = cast(Dict[str, Any], raw.get("author") or {})
            parents = cast(List[Dict[str, Any]], raw.get("parents") or [])
            commits.append(
                GithubCommit(
                    sha=sha,
                    parent_shas=tuple(
                        str(parent.get("sha", "")).strip()
                        for parent in parents
                        if parent.get("sha")
                    ),
                    authored_at=str(author_data.get("date", "")).strip(),
                    committed_at=str(committer_data.get("date", "")).strip(),
                    git_author=str(author_data.get("name", "")).strip(),
                    github_author=(str(github_author.get("login", "")).strip() or None),
                    message=str(commit_data.get("message", "")),
                    html_url=str(raw.get("html_url", "")).strip(),
                )
            )

        if not found_start:
            raise GithubApiError(
                "La borne de départ n'a pas été trouvée dans la plage bornée. "
                "Augmente max_commits ou corrige la borne."
            )

        commits.reverse()
        return commits

    def list_issues(
        self,
        full_name: Optional[str] = None,
        state: str = "open",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Liste les issues d'un repo (par défaut: ouvertes)."""
        repo_name = (full_name or GITHUB_REPO or "").strip()
        if not repo_name:
            raise ValueError(
                "Aucun repo spécifié. Passe full_name ou configure GITHUB_REPO dans le .env."
            )

        params = {
            "state": state,
            "per_page": min(limit, 100),
        }

        data = self._request("GET", f"/repos/{repo_name}/issues", params=params)
        issues = cast(List[Dict[str, Any]], data)

        cleaned: List[Dict[str, Any]] = []
        for issue in issues:
            # Les PR ont une clé "pull_request"
            if "pull_request" in issue:
                continue
            cleaned.append(
                {
                    "id": issue.get("id"),
                    "number": issue.get("number"),
                    "title": issue.get("title"),
                    "state": issue.get("state"),
                    "url": issue.get("html_url"),
                    "labels": [label.get("name") for label in issue.get("labels", [])],
                }
            )

        return cleaned


# ---------------------------------------------------------------------- #
#  Ping de santé pour l'API (compatible avec ton système existant)
# ---------------------------------------------------------------------- #


@trace_endpoint("github", catch=True)
def ping_github() -> PingResult:
    """Endpoint de santé GitHub utilisé par Hanuman."""
    service = GithubService()
    user = service.get_user()
    login = user.get("login", "inconnu")
    return PingResult(ok=True, source="github", detail={"login": login})
