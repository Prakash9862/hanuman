from __future__ import annotations

import httpx

from hanuman.core.logging import get_logger
from hanuman.models.ping import PingResult
from hanuman.utils.decorators import trace_endpoint

logger = get_logger(__name__)

ANKI_CONNECT_URL = "http://127.0.0.1:8765"


@trace_endpoint("anki", catch=True)
def ping_anki() -> PingResult:
    """Vérifie qu'AnkiConnect répond."""

    response = httpx.post(
        ANKI_CONNECT_URL,
        json={
            "action": "version",
            "version": 6,
        },
        timeout=5,
    )


def list_anki_decks() -> list[str]:
    """Retourne les noms des paquets Anki."""

    response = httpx.post(
        ANKI_CONNECT_URL,
        json={
            "action": "deckNames",
            "version": 6,
        },
        timeout=5,
    )

    response.raise_for_status()
    payload = response.json()

    if payload.get("error"):
        raise RuntimeError(payload["error"])

    result = payload.get("result")
    if not isinstance(result, list):
        raise RuntimeError("Réponse AnkiConnect invalide pour deckNames")

    return sorted(str(deck) for deck in result)