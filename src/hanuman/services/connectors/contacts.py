from __future__ import annotations

import json
import os
import secrets
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

import httpx

AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CONNECTIONS_URL = "https://people.googleapis.com/v1/people/me/connections"

CONTACTS_SCOPE = "https://www.googleapis.com/auth/contacts.readonly"

DEFAULT_REDIRECT_URI = "http://127.0.0.1:8000/resources/contacts/auth/callback"

TOKEN_PATH = Path(
    os.environ.get(
        "CONTACTS_TOKEN_PATH",
        ".secrets/contacts-token.json",
    )
)

STATE_PATH = Path(
    os.environ.get(
        "CONTACTS_STATE_PATH",
        ".secrets/contacts-oauth-state",
    )
)

CREDENTIALS_PATH = Path(
    os.environ.get(
        "CONTACTS_CREDENTIALS_PATH",
        "config/gmail_credentials.json",
    )
)

TOKEN_EXPIRY_MARGIN_SECONDS = 60


class ContactsConnectorError(RuntimeError):
    """Erreur fonctionnelle du connecteur Google Contacts."""


@dataclass(frozen=True, slots=True)
class GoogleContact:
    resource_name: str
    name: str
    given_name: str | None
    family_name: str | None
    emails: tuple[str, ...]
    phones: tuple[str, ...]
    organizations: tuple[str, ...]
    photo_url: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "resource_name": self.resource_name,
            "name": self.name,
            "given_name": self.given_name,
            "family_name": self.family_name,
            "emails": list(self.emails),
            "phones": list(self.phones),
            "organizations": list(self.organizations),
            "photo_url": self.photo_url,
        }


@dataclass(frozen=True, slots=True)
class ContactsPage:
    contacts: tuple[GoogleContact, ...]
    next_page_token: str | None
    total_items: int | None

    def to_dict(self) -> dict[str, object]:
        return {
            "contacts": [contact.to_dict() for contact in self.contacts],
            "next_page_token": self.next_page_token,
            "total_items": self.total_items,
        }


def _redirect_uri() -> str:
    return os.environ.get(
        "CONTACTS_REDIRECT_URI",
        DEFAULT_REDIRECT_URI,
    )


def _read_credentials_file() -> tuple[str, str] | None:
    if not CREDENTIALS_PATH.is_file():
        return None

    try:
        payload = json.loads(CREDENTIALS_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContactsConnectorError(f"Identifiants Google illisibles : {exc}") from exc

    if not isinstance(payload, dict):
        return None

    config = payload.get("web") or payload.get("installed") or payload

    if not isinstance(config, dict):
        return None

    client_id = config.get("client_id")
    client_secret = config.get("client_secret")

    if not client_id or not client_secret:
        return None

    return str(client_id), str(client_secret)


def _credentials() -> tuple[str, str]:
    client_id = os.environ.get("CONTACTS_CLIENT_ID") or os.environ.get("GMAIL_CLIENT_ID")
    client_secret = os.environ.get("CONTACTS_CLIENT_SECRET") or os.environ.get(
        "GMAIL_CLIENT_SECRET"
    )

    if client_id and client_secret:
        return client_id, client_secret

    file_credentials = _read_credentials_file()

    if file_credentials is not None:
        return file_credentials

    raise ContactsConnectorError(
        "Identifiants Google Contacts absents. "
        "Configure CONTACTS_CLIENT_ID et "
        "CONTACTS_CLIENT_SECRET, ou ajoute "
        "config/gmail_credentials.json."
    )


def _load_token() -> dict[str, Any]:
    if not TOKEN_PATH.is_file():
        raise ContactsConnectorError("Google Contacts n'est pas encore connecté.")

    try:
        payload = json.loads(TOKEN_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContactsConnectorError(f"Token Google Contacts illisible : {exc}") from exc

    if not isinstance(payload, dict):
        raise ContactsConnectorError("Le token Google Contacts est invalide.")

    return payload


def _save_token(
    token: dict[str, Any],
    *,
    previous_refresh_token: str | None = None,
) -> None:
    payload = dict(token)

    refresh_token = payload.get("refresh_token") or previous_refresh_token

    if refresh_token:
        payload["refresh_token"] = str(refresh_token)

    expires_in = int(payload.get("expires_in", 3600))
    payload["expires_at"] = time.time() + expires_in - TOKEN_EXPIRY_MARGIN_SECONDS

    TOKEN_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    TOKEN_PATH.write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    TOKEN_PATH.chmod(0o600)


def _save_oauth_state(state: str) -> None:
    STATE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    STATE_PATH.write_text(state, encoding="utf-8")
    STATE_PATH.chmod(0o600)


def _consume_oauth_state(received_state: str) -> None:
    if not STATE_PATH.is_file():
        raise ContactsConnectorError("État OAuth Contacts absent ou expiré.")

    expected_state = STATE_PATH.read_text(encoding="utf-8").strip()

    STATE_PATH.unlink(missing_ok=True)

    if not secrets.compare_digest(
        expected_state,
        received_state,
    ):
        raise ContactsConnectorError("État OAuth Contacts invalide.")


def build_authorization_url() -> str:
    client_id, _ = _credentials()
    state = secrets.token_urlsafe(32)

    _save_oauth_state(state)

    query = urlencode(
        {
            "client_id": client_id,
            "redirect_uri": _redirect_uri(),
            "response_type": "code",
            "scope": CONTACTS_SCOPE,
            "access_type": "offline",
            "include_granted_scopes": "true",
            "prompt": "consent",
            "state": state,
        }
    )

    return f"{AUTHORIZATION_URL}?{query}"


def exchange_authorization_code(
    code: str,
    state: str,
) -> None:
    _consume_oauth_state(state)

    client_id, client_secret = _credentials()

    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "code": code,
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": _redirect_uri(),
                "grant_type": "authorization_code",
            },
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise ContactsConnectorError(f"Impossible de contacter Google OAuth : {exc}") from exc

    if response.status_code != 200:
        raise ContactsConnectorError(
            "Échec de l'autorisation Google Contacts : " f"{response.status_code} {response.text}"
        )

    token = response.json()

    if not isinstance(token, dict):
        raise ContactsConnectorError("Réponse OAuth Google Contacts invalide.")

    if not token.get("access_token"):
        raise ContactsConnectorError("Google n'a pas renvoyé d'access_token.")

    _save_token(token)


def _refresh_access_token(
    tokens: dict[str, Any],
) -> str:
    refresh_token = tokens.get("refresh_token")

    if not refresh_token:
        raise ContactsConnectorError(
            "Le token Contacts a expiré et ne contient "
            "aucun refresh_token. Reconnecte Google Contacts."
        )

    client_id, client_secret = _credentials()

    try:
        response = httpx.post(
            TOKEN_URL,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "refresh_token": str(refresh_token),
                "grant_type": "refresh_token",
            },
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise ContactsConnectorError(f"Impossible de renouveler le token Contacts : {exc}") from exc

    if response.status_code != 200:
        raise ContactsConnectorError(
            "Échec du renouvellement Contacts : " f"{response.status_code} {response.text}"
        )

    refreshed = response.json()

    if not isinstance(refreshed, dict) or not refreshed.get("access_token"):
        raise ContactsConnectorError("Google n'a pas renvoyé de nouvel access_token.")

    _save_token(
        refreshed,
        previous_refresh_token=str(refresh_token),
    )

    return str(refreshed["access_token"])


def _access_token(
    *,
    force_refresh: bool = False,
) -> str:
    env_token = os.environ.get("CONTACTS_ACCESS_TOKEN")

    if env_token and not force_refresh:
        return env_token

    tokens = _load_token()

    if force_refresh:
        return _refresh_access_token(tokens)

    access_token = tokens.get("access_token")
    expires_at = tokens.get("expires_at")

    if access_token and expires_at is not None:
        try:
            still_valid = float(expires_at) > time.time()
        except (TypeError, ValueError):
            still_valid = False

        if still_valid:
            return str(access_token)

    return _refresh_access_token(tokens)


def _authorized_get(
    url: str,
    *,
    params: dict[str, str | int] | None = None,
) -> httpx.Response:
    try:
        response = httpx.get(
            url,
            params=params,
            headers={
                "Authorization": (f"Bearer {_access_token()}"),
                "Accept": "application/json",
            },
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise ContactsConnectorError(f"People API inaccessible : {exc}") from exc

    if response.status_code != 401:
        return response

    try:
        return httpx.get(
            url,
            params=params,
            headers={
                "Authorization": ("Bearer " f"{_access_token(force_refresh=True)}"),
                "Accept": "application/json",
            },
            timeout=20,
        )
    except httpx.HTTPError as exc:
        raise ContactsConnectorError(
            f"People API inaccessible après renouvellement : {exc}"
        ) from exc


def _first_string(
    values: object,
    field: str,
) -> str | None:
    if not isinstance(values, list):
        return None

    for item in values:
        if not isinstance(item, dict):
            continue

        value = item.get(field)

        if value:
            return str(value)

    return None


def _all_strings(
    values: object,
    field: str,
) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()

    result: list[str] = []

    for item in values:
        if not isinstance(item, dict):
            continue

        value = item.get(field)

        if value:
            normalized = str(value).strip()

            if normalized and normalized not in result:
                result.append(normalized)

    return tuple(result)


def _organization_names(
    values: object,
) -> tuple[str, ...]:
    if not isinstance(values, list):
        return ()

    result: list[str] = []

    for item in values:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        title = item.get("title")

        parts = [str(value).strip() for value in (name, title) if value]

        value = " — ".join(parts)

        if value and value not in result:
            result.append(value)

    return tuple(result)


def _parse_contact(
    person: dict[str, Any],
) -> GoogleContact:
    names = person.get("names")

    display_name = _first_string(
        names,
        "displayName",
    )
    given_name = _first_string(
        names,
        "givenName",
    )
    family_name = _first_string(
        names,
        "familyName",
    )

    emails = _all_strings(
        person.get("emailAddresses"),
        "value",
    )
    phones = _all_strings(
        person.get("phoneNumbers"),
        "value",
    )
    organizations = _organization_names(person.get("organizations"))
    photo_url = _first_string(
        person.get("photos"),
        "url",
    )

    fallback_name = emails[0] if emails else phones[0] if phones else "Contact sans nom"

    return GoogleContact(
        resource_name=str(person.get("resourceName", "")),
        name=display_name or fallback_name,
        given_name=given_name,
        family_name=family_name,
        emails=emails,
        phones=phones,
        organizations=organizations,
        photo_url=photo_url,
    )


class ContactsConnector:
    """Adaptateur HTTP de Google Contacts via People API."""

    def configured(self) -> bool:
        try:
            _credentials()
        except ContactsConnectorError:
            return False

        return True

    def connected(self) -> bool:
        try:
            self.list_contacts(page_size=1)
        except ContactsConnectorError:
            return False

        return True

    def list_contacts(
        self,
        *,
        page_size: int = 100,
        page_token: str | None = None,
    ) -> ContactsPage:
        bounded_page_size = max(
            1,
            min(page_size, 1000),
        )

        params: dict[str, str | int] = {
            "pageSize": bounded_page_size,
            "personFields": ("names,emailAddresses,phoneNumbers," "organizations,photos"),
        }

        if page_token:
            params["pageToken"] = page_token

        response = _authorized_get(
            CONNECTIONS_URL,
            params=params,
        )

        if response.status_code == 403:
            raise ContactsConnectorError(
                "Google refuse l'accès aux contacts. "
                "Vérifie que People API est activée et "
                "reconnecte le connecteur."
            )

        if response.status_code == 401:
            raise ContactsConnectorError(
                "Google Contacts refuse le token. " "Reconnecte le connecteur."
            )

        if response.status_code >= 400:
            raise ContactsConnectorError(
                "Erreur People API : " f"{response.status_code} {response.text}"
            )

        payload = response.json()

        if not isinstance(payload, dict):
            raise ContactsConnectorError("Réponse People API invalide.")

        raw_connections = payload.get(
            "connections",
            [],
        )

        contacts: list[GoogleContact] = []

        if isinstance(raw_connections, list):
            for item in raw_connections:
                if isinstance(item, dict):
                    contacts.append(_parse_contact(item))

        total_items = payload.get("totalItems")

        return ContactsPage(
            contacts=tuple(contacts),
            next_page_token=(
                str(payload["nextPageToken"]) if payload.get("nextPageToken") else None
            ),
            total_items=(int(total_items) if isinstance(total_items, int) else None),
        )

    def search_contacts(
        self,
        query: str,
        *,
        limit: int = 50,
    ) -> tuple[GoogleContact, ...]:
        normalized_query = query.strip().casefold()

        if not normalized_query:
            raise ValueError("La recherche Contacts ne peut pas être vide.")

        bounded_limit = max(1, min(limit, 200))
        matches: list[GoogleContact] = []
        page_token: str | None = None

        while len(matches) < bounded_limit:
            page = self.list_contacts(
                page_size=1000,
                page_token=page_token,
            )

            for contact in page.contacts:
                searchable_values = (
                    contact.name,
                    contact.given_name or "",
                    contact.family_name or "",
                    *contact.emails,
                    *contact.phones,
                    *contact.organizations,
                )

                if any(normalized_query in value.casefold() for value in searchable_values):
                    matches.append(contact)

                    if len(matches) >= bounded_limit:
                        break

            page_token = page.next_page_token

            if not page_token:
                break

        return tuple(matches)
