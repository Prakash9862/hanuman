from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import httpx

from hanuman.config.env import GITHUB_TOKEN, GITHUB_REPO
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
        self._token = token or GITHUB_TOKEN
        if not self._token:
            raise GithubAuthError(
                "GITHUB_TOKEN manquant. Configure-le dans le .env ou passe-le au constructeur."
            )

        self._headers = {
            "Authorization": f"token {self._token}",
            "Accept": "application/vnd.github+json",
        }

    def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
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

        return response

    # ------------------------------------------------------------------ #
    #  Méthodes publiques
    # ------------------------------------------------------------------ #

    def get_user(self) -> Dict[str, Any]:
        """Retourne les infos du user GitHub lié au token."""
        r = self._request("GET", "/user")
        return r.json()

    def get_repo(self, full_name: Optional[str] = None) -> GithubRepo:
        """Retourne les infos d'un repo (ex: 'Prakash9862/hanuman')."""
        repo_name = full_name or GITHUB_REPO
        if not repo_name:
            raise ValueError(
                "Aucun repo spécifié. Passe full_name ou configure GITHUB_REPO dans le .env."
            )

        r = self._request("GET", f"/repos/{repo_name}")
        data = r.json()

        return GithubRepo(
            full_name=data.get("full_name", repo_name),
            description=data.get("description") or "",
            stars=int(data.get("stargazers_count", 0)),
            forks=int(data.get("forks_count", 0)),
            html_url=data.get("html_url", ""),
            default_branch=data.get("default_branch", "main"),
        )

    def list_issues(
        self,
        full_name: Optional[str] = None,
        state: str = "open",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """Liste les issues d'un repo (par défaut: ouvertes)."""
        repo_name = full_name or GITHUB_REPO
        if not repo_name:
            raise ValueError(
                "Aucun repo spécifié. Passe full_name ou configure GITHUB_REPO dans le .env."
            )

        params = {
            "state": state,
            "per_page": min(limit, 100),
        }

        r = self._request("GET", f"/repos/{repo_name}/issues", params=params)
        issues = r.json()

        # On ne garde que les issues "pures" (on filtre les PR si nécessaire)
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
                    "labels": [l.get("name") for l in issue.get("labels", [])],
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
