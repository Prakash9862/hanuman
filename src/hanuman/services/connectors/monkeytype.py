from __future__ import annotations

import httpx


class MonkeytypeConnector:
    """Connecteur HTTP vers l'API Monkeytype."""

    def __init__(self, base_url: str, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.token = token

    def healthcheck(self) -> bool:
        return bool(self.base_url)

    def get_profile(self, username: str) -> dict[str, object]:
        response = httpx.get(
            f"{self.base_url}/users/{username}/profile",
            timeout=15,
        )
        response.raise_for_status()
        payload = response.json()

        if not isinstance(payload, dict):
            raise TypeError("Réponse Monkeytype invalide")

        return payload
