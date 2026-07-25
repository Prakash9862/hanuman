from __future__ import annotations

import types
from typing import Any

import pytest

from hanuman.models.ping import PingResult
from hanuman.services.core import calendar_service


class DummyResponse:
    """Réponse HTTP factice compatible avec le code Calendar."""

    def __init__(
        self,
        status_code: int,
        json_data: dict[str, Any] | None = None,
        text: str = "",
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._json_data

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}: {self.text}")


# ------------------------------------------------------------------
# exchange_code_for_token
# ------------------------------------------------------------------


def test_exchange_code_for_token_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un code OAuth valide est échangé puis sauvegardé."""

    saved: dict[str, Any] = {}

    def fake_post(
        url: str,
        data: dict[str, Any],
        timeout: int,
    ) -> DummyResponse:
        assert url == calendar_service.GOOGLE_TOKEN_URL
        assert data["code"] == "dummy-code"
        assert "client_id" in data
        assert "client_secret" in data
        assert "redirect_uri" in data
        assert data["grant_type"] == "authorization_code"
        assert timeout == 15

        return DummyResponse(
            200,
            json_data={
                "access_token": "tok",
                "refresh_token": "ref",
            },
        )

    def fake_save_token_json(
        name: str,
        token_data: dict[str, Any],
    ) -> None:
        assert name == "google_calendar"
        saved.update(token_data)

    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(post=fake_post),
    )
    monkeypatch.setattr(
        calendar_service,
        "save_token_json",
        fake_save_token_json,
    )

    result = calendar_service.exchange_code_for_token("dummy-code")

    assert result is True
    assert saved["access_token"] == "tok"
    assert saved["refresh_token"] == "ref"
    assert isinstance(saved["expires_at"], float)


def test_exchange_code_for_token_invalid_code(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un code OAuth invalide renvoie un PingResult en erreur."""

    def fake_post(
        url: str,
        data: dict[str, Any],
        timeout: int,
    ) -> DummyResponse:
        return DummyResponse(
            400,
            text="invalid_grant",
        )

    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(post=fake_post),
    )

    result = calendar_service.exchange_code_for_token("bad-code")

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error is not None
    assert "Code OAuth expiré ou invalide" in result.error
    assert "invalid_grant" in result.error


def test_exchange_code_for_token_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une erreur du serveur OAuth produit un PingResult en erreur."""

    def fake_post(
        url: str,
        data: dict[str, Any],
        timeout: int,
    ) -> DummyResponse:
        return DummyResponse(
            503,
            text="backend down",
        )

    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(post=fake_post),
    )

    result = calendar_service.exchange_code_for_token("any")

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error is not None
    assert "Erreur OAuth Calendar" in result.error
    assert "503" in result.error
    assert "backend down" in result.error


# ------------------------------------------------------------------
# get_calendar_list
# ------------------------------------------------------------------


def test_get_calendar_list_no_token(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """L'absence d'access_token est signalée clairement."""

    def fake_load_token_json(
        name: str,
    ) -> dict[str, Any]:
        assert name == "google_calendar"
        return {}

    monkeypatch.setattr(
        calendar_service,
        "load_token_json",
        fake_load_token_json,
    )

    result = calendar_service.get_calendar_list()

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error == ("Calendar non connecté : aucun access_token trouvé")


def test_get_calendar_list_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """La liste Calendar est récupérée avec le bon token."""

    def fake_load_token_json(
        name: str,
    ) -> dict[str, Any]:
        assert name == "google_calendar"
        return {"access_token": "abc"}

    def fake_get(
        url: str,
        headers: dict[str, str],
        timeout: int,
        params: dict[str, Any] | None = None,
    ) -> DummyResponse:
        assert url == calendar_service.CALENDAR_LIST_URL
        assert headers["Authorization"] == "Bearer abc"
        assert headers["Accept"] == "application/json"
        assert timeout == 15

        return DummyResponse(
            200,
            json_data={
                "items": [
                    {
                        "id": "primary",
                        "summary": "Principal",
                        "primary": True,
                        "accessRole": "owner",
                    },
                    {
                        "id": "work",
                        "summary": "Travail",
                        "primary": False,
                        "accessRole": "reader",
                    },
                    {
                        "id": "other",
                        "summary": "Autre",
                    },
                ]
            },
        )

    monkeypatch.setattr(
        calendar_service,
        "load_token_json",
        fake_load_token_json,
    )
    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(get=fake_get),
    )

    result = calendar_service.get_calendar_list()

    assert isinstance(result, PingResult)
    assert result.ok is True
    assert result.source == "calendar"
    assert result.detail == {
        "calendar_count": 3,
    }


def test_get_calendar_list_unauthorized(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Un token Google expiré est correctement signalé."""

    def fake_load_token_json(
        name: str,
    ) -> dict[str, Any]:
        return {"access_token": "expired"}

    def fake_get(
        url: str,
        headers: dict[str, str],
        timeout: int,
        params: dict[str, Any] | None = None,
    ) -> DummyResponse:
        return DummyResponse(
            401,
            text="invalid_token",
        )

    monkeypatch.setattr(
        calendar_service,
        "load_token_json",
        fake_load_token_json,
    )
    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(get=fake_get),
    )

    result = calendar_service.get_calendar_list()

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error is not None
    assert "aucun refresh_token" in result.error
    assert "nouvelle connexion Google" in result.error

def test_get_calendar_list_server_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Une erreur HTTP Google est transformée en PingResult en erreur."""

    def fake_load_token_json(
        name: str,
    ) -> dict[str, Any]:
        return {"access_token": "tok"}

    def fake_get(
        url: str,
        headers: dict[str, str],
        timeout: int,
        params: dict[str, Any] | None = None,
    ) -> DummyResponse:
        return DummyResponse(
            500,
            text="boom",
        )

    monkeypatch.setattr(
        calendar_service,
        "load_token_json",
        fake_load_token_json,
    )
    monkeypatch.setattr(
        calendar_service,
        "httpx",
        types.SimpleNamespace(get=fake_get),
    )

    result = calendar_service.get_calendar_list()

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error == "HTTP 500: boom"
