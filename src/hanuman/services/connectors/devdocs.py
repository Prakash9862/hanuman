from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx


class DevdocsConnectorError(RuntimeError):
    """Erreur rencontrée pendant un échange avec DevDocs."""


class DevdocsConnector:
    """Adaptateur HTTP bas niveau vers DevDocs."""

    def __init__(
        self,
        base_url: str = "https://devdocs.io",
        *,
        timeout: float = 10.0,
        client: httpx.Client | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client

        return httpx.Client(
            base_url=self.base_url,
            timeout=self.timeout,
            follow_redirects=True,
            headers={
                "Accept": "application/json",
                "User-Agent": "Hanuman/DevDocsConnector",
            },
        )

    def healthcheck(self) -> bool:
        """Vérifie que le manifeste DevDocs est réellement accessible."""

        try:
            self.list_documentations()
        except (DevdocsConnectorError, httpx.HTTPError):
            return False

        return True

    def list_documentations(self) -> list[dict[str, Any]]:
        """Récupère le catalogue public des documentations DevDocs."""

        client = self._get_client()

        try:
            response = client.get("/docs.json")
            response.raise_for_status()
            payload = response.json()
        except (httpx.HTTPError, ValueError) as exc:
            raise DevdocsConnectorError(
                f"Impossible de récupérer le catalogue DevDocs : {exc}"
            ) from exc

        if not isinstance(payload, list):
            raise DevdocsConnectorError("Le catalogue DevDocs possède un format inattendu.")

        return [item for item in payload if isinstance(item, dict)]

    def build_home_url(self) -> str:
        """Retourne l'adresse principale de DevDocs."""

        return f"{self.base_url}/"

    def build_search_url(self, query: str) -> str:
        """Construit une URL ouvrant la recherche dans DevDocs."""

        normalized_query = query.strip()
        if not normalized_query:
            return self.build_home_url()

        return f"{self.base_url}/#q={quote(normalized_query)}"
