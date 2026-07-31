from __future__ import annotations

from dataclasses import dataclass

from hanuman.services.connectors.contacts import (
    ContactsConnector,
    ContactsConnectorError,
    ContactsPage,
    GoogleContact,
    build_authorization_url,
    exchange_authorization_code,
)


@dataclass(frozen=True, slots=True)
class ContactsStatus:
    ok: bool
    configured: bool
    connected: bool
    message: str | None = None


def _connector() -> ContactsConnector:
    return ContactsConnector()


def ping_contacts() -> ContactsStatus:
    """Retourne l'état réel du connecteur Google Contacts."""

    connector = _connector()

    if not connector.configured():
        return ContactsStatus(
            ok=False,
            configured=False,
            connected=False,
            message=("Identifiants Google Contacts absents."),
        )

    try:
        connector.list_contacts(page_size=1)
    except ContactsConnectorError as exc:
        return ContactsStatus(
            ok=False,
            configured=True,
            connected=False,
            message=str(exc),
        )

    return ContactsStatus(
        ok=True,
        configured=True,
        connected=True,
        message=None,
    )


def get_contacts_authorization_url() -> str:
    return build_authorization_url()


def connect_contacts(
    code: str,
    state: str,
) -> None:
    exchange_authorization_code(
        code=code,
        state=state,
    )


def list_google_contacts(
    *,
    page_size: int = 100,
    page_token: str | None = None,
) -> ContactsPage:
    return _connector().list_contacts(
        page_size=page_size,
        page_token=page_token,
    )


def search_google_contacts(
    query: str,
    *,
    limit: int = 50,
) -> tuple[GoogleContact, ...]:
    return _connector().search_contacts(
        query,
        limit=limit,
    )
