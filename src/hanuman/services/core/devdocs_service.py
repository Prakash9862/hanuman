from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DevdocsStatus:
    ok: bool
    configured: bool
    message: str | None = None


def ping_devdocs() -> DevdocsStatus:
    """Retourne l'état minimal du connecteur DevDocs."""

    return DevdocsStatus(
        ok=True,
        configured=True,
        message=None,
    )
