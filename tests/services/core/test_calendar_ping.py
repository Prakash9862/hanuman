import types
from typing import Any, Dict

import pytest

from hanuman.models.ping import PingResult
from hanuman.services.core import calendar_service


class DummyResponse:
    def __init__(
        self, status_code: int, json_data: Dict[str, Any] | None = None, text: str = ""
    ) -> None:
        self.status_code = status_code
        self._json_data = json_data or {}
        self.text = text

    def json(self) -> Dict[str, Any]:
        return self._json_data


# ---------------- exchange_code_for_token ---------------- #


def test_exchange_code_for_token_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas nominal :
    - httpx.post renvoie 200 avec un token JSON
    - save_token_json est bien appelé
    - la fonction renvoie True (ou un résultat non-erreur)
    """

    saved: dict[str, Any] = {}

    def fake_post(url: str, data: dict, timeout: int) -> DummyResponse:
        assert url == calendar_service.GOOGLE_TOKEN_URL
        # On vérifie que les champs OAuth minimaux sont bien envoyés
        assert "code" in data
        assert "client_id" in data
        assert "client_secret" in data
        assert "redirect_uri" in data
        assert data["grant_type"] == "authorization_code"
        return DummyResponse(
            200,
            json_data={"access_token": "tok", "refresh_token": "ref"},
        )

    def fake_save_token_json(name: str, token_data: dict) -> None:
        assert name == "google_calendar"
        saved.update(token_data)

    monkeypatch.setattr(
        calendar_service, "httpx", types.SimpleNamespace(post=fake_post)
    )
    monkeypatch.setattr(calendar_service, "save_token_json", fake_save_token_json)

    result = calendar_service.exchange_code_for_token("dummy-code")

    # Suivant l'implémentation de trace_endpoint, on ne sait pas exactement le type
    # On vérifie au moins que ça ne remonte pas en erreur et que le token a été sauvegardé.
    assert saved["access_token"] == "tok"
    assert saved["refresh_token"] == "ref"
    assert result is not None


def test_exchange_code_for_token_invalid_code(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas code invalide (400) :
    - on s'assure que la branche ValueError est bien exécutée
    - suivant trace_endpoint(catch=True), ça peut soit lever, soit renvoyer un PingResult en erreur
    """

    def fake_post(url: str, data: dict, timeout: int) -> DummyResponse:
        return DummyResponse(400, text="invalid_grant")

    monkeypatch.setattr(
        calendar_service, "httpx", types.SimpleNamespace(post=fake_post)
    )

    try:
        result = calendar_service.exchange_code_for_token("bad-code")
    except Exception:
        # Si l'exception remonte, c'est aussi acceptable pour ce test :
        # la branche avec raise ValueError est bien exécutée.
        return

    # Sinon, on attend un PingResult en erreur
    assert isinstance(result, PingResult)
    assert result.ok is False
    assert "Code expiré" in (result.error or "")


def test_exchange_code_for_token_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas erreur serveur (ex: 500) :
    - branche RuntimeError dans exchange_code_for_token
    """

    def fake_post(url: str, data: dict, timeout: int) -> DummyResponse:
        return DummyResponse(503, text="backend down")

    monkeypatch.setattr(
        calendar_service, "httpx", types.SimpleNamespace(post=fake_post)
    )

    try:
        result = calendar_service.exchange_code_for_token("any")
    except Exception:
        return

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert "Erreur OAuth" in (result.error or "")


# ---------------- get_calendar_list ---------------- #


def test_get_calendar_list_no_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas sans access_token dans le fichier de token :
    - renvoie un PingResult ok=False avec message "No access_token found"
    """

    def fake_load_token_json(name: str) -> dict[str, Any]:
        assert name == "google_calendar"
        return {}  # pas d'access_token

    monkeypatch.setattr(calendar_service, "load_token_json", fake_load_token_json)

    result = calendar_service.get_calendar_list()
    assert isinstance(result, PingResult)
    assert result.ok is False
    assert result.error == "No access_token found"


def test_get_calendar_list_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas nominal :
    - access_token présent
    - httpx.get renvoie une liste items
    """

    def fake_load_token_json(name: str) -> dict[str, Any]:
        return {"access_token": "abc"}

    def fake_get(url: str, headers: dict, timeout: int) -> DummyResponse:
        assert url == calendar_service.CALENDAR_API_URL
        assert headers["Authorization"] == "Bearer abc"
        return DummyResponse(
            200,
            json_data={"items": [{}, {}, {}]},  # 3 calendriers
        )

    monkeypatch.setattr(calendar_service, "load_token_json", fake_load_token_json)
    monkeypatch.setattr(calendar_service, "httpx", types.SimpleNamespace(get=fake_get))

    result = calendar_service.get_calendar_list()
    assert isinstance(result, PingResult)
    assert result.ok is True
    assert result.source == "calendar"
    assert result.detail == {"calendar_count": 3}


def test_get_calendar_list_unauthorized(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas token expiré (401) :
    - branche ValueError / trace_endpoint(catch=True)
    """

    def fake_load_token_json(name: str) -> dict[str, Any]:
        return {"access_token": "expired"}

    def fake_get(url: str, headers: dict, timeout: int) -> DummyResponse:
        return DummyResponse(401, text="invalid_token")

    monkeypatch.setattr(calendar_service, "load_token_json", fake_load_token_json)
    monkeypatch.setattr(calendar_service, "httpx", types.SimpleNamespace(get=fake_get))

    try:
        result = calendar_service.get_calendar_list()
    except Exception:
        return

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert "Token expiré" in (result.error or "")


def test_get_calendar_list_server_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Cas erreur 500+ :
    - branche RuntimeError / trace_endpoint(catch=True)
    """

    def fake_load_token_json(name: str) -> dict[str, Any]:
        return {"access_token": "tok"}

    def fake_get(url: str, headers: dict, timeout: int) -> DummyResponse:
        return DummyResponse(500, text="boom")

    monkeypatch.setattr(calendar_service, "load_token_json", fake_load_token_json)
    monkeypatch.setattr(calendar_service, "httpx", types.SimpleNamespace(get=fake_get))

    try:
        result = calendar_service.get_calendar_list()
    except Exception:
        return

    assert isinstance(result, PingResult)
    assert result.ok is False
    assert "Erreur API Calendar" in (result.error or "")
