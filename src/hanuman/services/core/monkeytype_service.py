from __future__ import annotations

from dataclasses import dataclass

from hanuman.services.connectors.monkeytype import MonkeytypeConnector


@dataclass(frozen=True, slots=True)
class MonkeytypeStatus:
    ok: bool
    configured: bool
    message: str | None = None


def ping_monkeytype() -> MonkeytypeStatus:
    connector = MonkeytypeConnector("https://api.monkeytype.com")

    return MonkeytypeStatus(
        ok=connector.healthcheck(),
        configured=True,
        message=None,
    )


def get_monkeytype_profile(username: str) -> dict[str, object]:
    normalized = username.strip()

    if not normalized:
        raise ValueError("Le nom d'utilisateur Monkeytype est obligatoire.")

    connector = MonkeytypeConnector("https://api.monkeytype.com")
    return connector.get_profile(normalized)
