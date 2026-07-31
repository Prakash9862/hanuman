from __future__ import annotations

from typing import Any

import pytest
from fastapi.testclient import TestClient

from hanuman.api.core.main import app
from hanuman.models.registry import RegistrySnapshot, RegistryState
from hanuman.services import settings_service

client = TestClient(app)


@pytest.fixture
def fake_programs() -> list[dict[str, Any]]:
    return [
        {
            "id": "stockfish",
            "label": "Stockfish",
            "ok": True,
            "installed": True,
            "path": "/usr/games/stockfish",
            "version": "Stockfish 17",
            "message": "Programme disponible",
        },
        {
            "id": "ffmpeg",
            "label": "FFmpeg",
            "ok": False,
            "installed": False,
            "path": None,
            "version": None,
            "message": "Programme non installé",
        },
    ]


def configure_settings_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    monkeypatch.setattr(settings_service.env, "APP_ENV", "test")
    monkeypatch.setattr(settings_service.env, "LOG_LEVEL", "DEBUG")
    monkeypatch.setattr(
        settings_service.env,
        "BASE_URL",
        "http://127.0.0.1:8000",
    )

    monkeypatch.setattr(
        settings_service.env,
        "NOTION_TOKEN",
        "api-secret-notion-token",
    )
    monkeypatch.setattr(
        settings_service.env,
        "GITHUB_TOKEN",
        "api-secret-github-token",
    )
    monkeypatch.setattr(
        settings_service.env,
        "OPENAI_API_KEY",
        "api-secret-openai-key",
    )
    monkeypatch.setattr(
        settings_service.env,
        "GOOGLE_CLIENT_ID",
        "api-google-client-id",
    )
    monkeypatch.setattr(
        settings_service.env,
        "CHESS_COM_USERNAME",
        "prakasch",
    )

    monkeypatch.setattr(
        settings_service,
        "list_connectors",
        lambda: [],
    )
    monkeypatch.setattr(
        settings_service,
        "inspect_programs",
        lambda: fake_programs,
    )

    monkeypatch.setattr(
        settings_service,
        "get_flows_registry",
        lambda: RegistrySnapshot(
            id="flows",
            label="Flux",
            state=RegistryState.NOT_IMPLEMENTED,
            implemented=False,
            entries=[],
            message="Aucun registre backend de flux n’est encore implémenté.",
        ),
    )

    monkeypatch.setattr(
        settings_service,
        "get_journal_registry",
        lambda: RegistrySnapshot(
            id="journal",
            label="Journal de Vie",
            state=RegistryState.NOT_IMPLEMENTED,
            implemented=False,
            entries=[],
            message="Le Journal de Vie ne possède pas encore de registre backend.",
        ),
    )

    monkeypatch.setattr(
        settings_service,
        "get_agents_registry",
        lambda: RegistrySnapshot(
            id="agents",
            label="Agents IA",
            state=RegistryState.NOT_IMPLEMENTED,
            implemented=False,
            entries=[],
            message="Aucun agent backend n’est encore enregistré.",
        ),
    )


def test_get_settings_returns_200(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")

    assert response.status_code == 200


def test_get_settings_returns_expected_sections(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")
    body = response.json()

    assert response.status_code == 200

    assert "general" in body
    assert "connectors" in body
    assert "programs" in body
    assert "flows" in body
    assert "journal" in body
    assert "agents" in body
    assert "diagnostic" in body
    assert "about" in body


def test_get_settings_reports_unimplemented_domains_honestly(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")
    body = response.json()

    assert response.status_code == 200

    assert body["flows"]["implemented"] is False
    assert body["flows"]["state"] == "not_implemented"
    assert body["flows"]["entries"] == []

    assert body["journal"]["implemented"] is False
    assert body["journal"]["state"] == "not_implemented"
    assert body["journal"]["entries"] == []

    assert body["agents"]["implemented"] is False
    assert body["agents"]["state"] == "not_implemented"
    assert body["agents"]["entries"] == []


def test_get_settings_returns_real_program_information(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")
    body = response.json()

    assert response.status_code == 200
    assert len(body["programs"]) == 2

    stockfish = next(program for program in body["programs"] if program["id"] == "stockfish")
    ffmpeg = next(program for program in body["programs"] if program["id"] == "ffmpeg")

    assert stockfish["installed"] is True
    assert stockfish["path"] == "/usr/games/stockfish"

    assert ffmpeg["installed"] is False
    assert ffmpeg["path"] is None


def test_get_settings_never_exposes_secret_values(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")

    assert response.status_code == 200

    body_text = response.text

    assert "api-secret-notion-token" not in body_text
    assert "api-secret-github-token" not in body_text
    assert "api-secret-openai-key" not in body_text
    assert "api-google-client-id" not in body_text

    assert "NOTION_TOKEN" in body_text
    assert "GITHUB_TOKEN" in body_text
    assert "OPENAI_API_KEY" in body_text


def test_get_settings_diagnostic_counts_programs(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
) -> None:
    configure_settings_dependencies(monkeypatch, fake_programs)

    response = client.get("/settings")
    body = response.json()

    assert response.status_code == 200

    diagnostic = body["diagnostic"]

    assert diagnostic["api_ok"] is True
    assert diagnostic["connectors_total"] == 0
    assert diagnostic["programs_total"] == 2
    assert diagnostic["programs_available"] == 1
