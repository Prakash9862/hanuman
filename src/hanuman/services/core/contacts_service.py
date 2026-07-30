from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ContactsStatus:
    ok: bool
    configured: bool
    message: str | None = None


def ping_contacts() -> ContactsStatus:
    """Retourne l'état minimal du connecteur Google Contacts."""

    return ContactsStatus(
        ok=True,
        configured=True,
        message=None,
    )
