import pytest
from fastapi.testclient import TestClient

from hanuman.core.config import settings
from hanuman.main import app

client = TestClient(app)


def test_calendar_auth_redirect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(settings, "google_client_id", "client-id")
    monkeypatch.setattr(settings, "google_redirect_uri", "https://example.com/callback")

    response = client.get("/calendar/auth", follow_redirects=False)

    assert response.status_code in {302, 307}
    expected_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        "?client_id=client-id"
        "&redirect_uri=https://example.com/callback"
        "&response_type=code"
        "&scope=https://www.googleapis.com/auth/calendar.readonly"
        "&access_type=offline"
        "&prompt=consent"
    )
    assert response.headers["location"] == expected_url


def test_calendar_callback_missing_code() -> None:
    response = client.get("/calendar/callback")

    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "Missing code"}


def test_calendar_callback_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "hanuman.api.core.calendar.exchange_code_for_token",
        lambda code: code == "valid",
    )

    response = client.get("/calendar/callback", params={"code": "valid"})

    assert response.status_code == 200
    assert response.json() == {"ok": True, "message": "Token reçu et stocké 🎉"}


def test_calendar_callback_failure(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "hanuman.api.core.calendar.exchange_code_for_token", lambda code: False
    )

    response = client.get("/calendar/callback", params={"code": "invalid"})

    assert response.status_code == 200
    assert response.json() == {"ok": False, "error": "Échec de l’échange de code"}
