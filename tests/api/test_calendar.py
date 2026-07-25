from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import pytest
from fastapi.testclient import TestClient

import hanuman.api.core.calendar as calendar_api
from hanuman.core.config import settings
from hanuman.main import app

client = TestClient(app)


def test_calendar_auth_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    """La route /calendar/auth construit correctement l'URL OAuth Google."""

    monkeypatch.setattr(
        settings,
        "google_calendar_client_id",
        "client-id",
    )
    monkeypatch.setattr(
        settings,
        "google_calendar_redirect_uri",
        "https://example.com/callback",
    )

    response = client.get("/calendar/auth", follow_redirects=False)

    assert response.status_code in {302, 307}

    location = response.headers["location"]
    parsed = urlparse(location)
    query = parse_qs(parsed.query)

    assert parsed.scheme == "https"
    assert parsed.netloc == "accounts.google.com"
    assert parsed.path == "/o/oauth2/v2/auth"

    assert query["client_id"] == ["client-id"]
    assert query["redirect_uri"] == ["https://example.com/callback"]
    assert query["response_type"] == ["code"]
    assert query["scope"] == ["https://www.googleapis.com/auth/calendar.readonly"]
    assert query["access_type"] == ["offline"]
    assert query["prompt"] == ["consent"]


def test_calendar_callback_google_error() -> None:
    """Une erreur renvoyée par Google produit une réponse HTTP 400."""

    response = client.get(
        "/calendar/callback",
        params={"error": "access_denied"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "error": "access_denied",
    }


def test_calendar_callback_missing_code() -> None:
    """L'absence de code OAuth produit une réponse HTTP 400."""

    response = client.get("/calendar/callback")

    assert response.status_code == 400
    assert response.json() == {
        "ok": False,
        "error": "Missing code",
    }


def test_calendar_callback_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un échange OAuth réussi confirme la connexion Calendar."""

    monkeypatch.setattr(
        calendar_api,
        "exchange_code_for_token",
        lambda code: code == "valid",
    )

    response = client.get(
        "/calendar/callback",
        params={"code": "valid"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "message": "Google Calendar est connecté à Hanuman.",
    }


def test_calendar_callback_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un échec d'échange OAuth produit une réponse HTTP 500."""

    monkeypatch.setattr(
        calendar_api,
        "exchange_code_for_token",
        lambda code: False,
    )

    response = client.get(
        "/calendar/callback",
        params={"code": "invalid"},
    )

    assert response.status_code == 500
    assert response.json() == {
        "ok": False,
        "error": "Échec de l’échange du code OAuth",
    }
