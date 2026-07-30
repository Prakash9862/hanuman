from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from hanuman.services.connectors.devdocs import (
    DevdocsConnector,
    DevdocsConnectorError,
)


@dataclass(frozen=True, slots=True)
class DevdocsStatus:
    ok: bool
    configured: bool
    message: str | None = None
    url: str | None = None


@dataclass(frozen=True, slots=True)
class DevdocsDocumentation:
    slug: str
    name: str
    version: str | None
    release: str | None
    updated_at: str | None
    icon: str | None

    def to_dict(self) -> dict[str, str | None]:
        return {
            "slug": self.slug,
            "name": self.name,
            "version": self.version,
            "release": self.release,
            "updated_at": self.updated_at,
            "icon": self.icon,
        }


def _connector() -> DevdocsConnector:
    return DevdocsConnector()


def ping_devdocs() -> DevdocsStatus:
    """Vérifie réellement la disponibilité du catalogue DevDocs."""

    connector = _connector()

    try:
        connector.list_documentations()
    except DevdocsConnectorError as exc:
        return DevdocsStatus(
            ok=False,
            configured=True,
            message=str(exc),
            url=connector.build_home_url(),
        )

    return DevdocsStatus(
        ok=True,
        configured=True,
        message=None,
        url=connector.build_home_url(),
    )


def list_devdocs_documentations() -> list[DevdocsDocumentation]:
    """Retourne un catalogue normalisé et trié pour Hanuman."""

    raw_documentations = _connector().list_documentations()
    documentations: list[DevdocsDocumentation] = []

    for item in raw_documentations:
        slug = _string_value(item, "slug")
        name = _string_value(item, "name")

        if slug is None or name is None:
            continue

        documentations.append(
            DevdocsDocumentation(
                slug=slug,
                name=name,
                version=_string_value(item, "version"),
                release=_string_value(item, "release"),
                updated_at=_string_value(item, "mtime"),
                icon=_string_value(item, "icon"),
            )
        )

    return sorted(
        documentations,
        key=lambda documentation: documentation.name.casefold(),
    )


def build_devdocs_search(query: str) -> dict[str, str]:
    """Prépare l'ouverture d'une recherche sur le site DevDocs."""

    normalized_query = query.strip()
    if not normalized_query:
        raise ValueError("La recherche DevDocs ne peut pas être vide.")

    connector = _connector()

    return {
        "query": normalized_query,
        "url": connector.build_search_url(normalized_query),
    }


def _string_value(item: dict[str, Any], key: str) -> str | None:
    value = item.get(key)

    if value is None:
        return None

    if isinstance(value, str):
        return value

    if isinstance(value, (int, float)):
        return str(value)

    return None
