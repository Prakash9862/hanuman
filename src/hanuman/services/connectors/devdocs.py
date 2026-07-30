from __future__ import annotations


class DevdocsConnector:
    """Adaptateur HTTP initial du connecteur DevDocs."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def healthcheck(self) -> bool:
        """Vérifie minimalement que le connecteur est configuré."""

        return bool(self.base_url)
