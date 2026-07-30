from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MonkeytypeStatus:
    ok: bool
    configured: bool
    message: str | None = None


def ping_monkeytype() -> MonkeytypeStatus:
    """Retourne l'état minimal du connecteur Monkeytype."""

    return MonkeytypeStatus(
        ok=True,
        configured=True,
        message=None,
    )
