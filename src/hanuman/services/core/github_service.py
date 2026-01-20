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
    full_name: str
    description: str
    stars: int
    forks: int
    html_url: str
    default_branch: str


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
            raise GithubApiError(
                f"Erreur GitHub {response.status_code}: {response.text}"
            )

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
            full_name=repo.get("full_name", repo_name),
            description=repo.get("description") or "",
            stars=int(repo.get("stargazers_count", 0)),
            forks=int(repo.get("forks_count", 0)),
            html_url=repo.get("html_url", ""),
            default_branch=repo.get("default_branch", "main"),
        )

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

    def list_repos(
        self,
        visibility: str = "all",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Liste les repositories accessibles au token."""
        params = {
            "visibility": visibility,
            "per_page": min(limit, 100),
            "sort": "updated",
        }

        data = self._request("GET", "/user/repos", params=params)
        repos = cast(List[Dict[str, Any]], data)

        cleaned: List[Dict[str, Any]] = []
        for repo in repos:
            cleaned.append(
                {
                    "id": repo.get("id"),
                    "full_name": repo.get("full_name"),
                    "description": repo.get("description") or "",
                    "html_url": repo.get("html_url"),
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "private": repo.get("private", False),
                    "updated_at": repo.get("updated_at"),
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
