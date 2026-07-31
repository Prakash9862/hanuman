from __future__ import annotations

from typing import Any

import pytest

from hanuman.models.registry import RegistrySnapshot, RegistryState
from hanuman.services import settings_service


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


@pytest.fixture
def empty_flows_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="flows",
        label="Flux",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Aucun registre backend de flux n’est encore implémenté.",
    )


@pytest.fixture
def empty_journal_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="journal",
        label="Journal de Vie",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Le Journal de Vie ne possède pas encore de registre backend.",
    )


@pytest.fixture
def empty_agents_registry() -> RegistrySnapshot:
    return RegistrySnapshot(
        id="agents",
        label="Agents IA",
        state=RegistryState.NOT_IMPLEMENTED,
        implemented=False,
        entries=[],
        message="Aucun agent backend n’est encore enregistré.",
    )


def configure_fake_environment(monkeypatch: pytest.MonkeyPatch) -> None:
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
        "secret-notion-token",
    )
    monkeypatch.setattr(
        settings_service.env,
        "GITHUB_TOKEN",
        "secret-github-token",
    )
    monkeypatch.setattr(
        settings_service.env,
        "OPENAI_API_KEY",
        "secret-openai-key",
    )
    monkeypatch.setattr(
        settings_service.env,
        "GOOGLE_CLIENT_ID",
        "google-client-id",
    )
    monkeypatch.setattr(
        settings_service.env,
        "CHESS_COM_USERNAME",
        "prakasch",
    )


def configure_fake_dependencies(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
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
        lambda: empty_flows_registry,
    )
    monkeypatch.setattr(
        settings_service,
        "get_journal_registry",
        lambda: empty_journal_registry,
    )
    monkeypatch.setattr(
        settings_service,
        "get_agents_registry",
        lambda: empty_agents_registry,
    )


def test_build_settings_snapshot_aggregates_existing_sources(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
    configure_fake_environment(monkeypatch)
    configure_fake_dependencies(
        monkeypatch,
        fake_programs,
        empty_flows_registry,
        empty_journal_registry,
        empty_agents_registry,
    )

    snapshot = settings_service.build_settings_snapshot()

    assert snapshot.general.app_env == "test"
    assert snapshot.general.log_level == "DEBUG"
    assert snapshot.general.api_base_url == "http://127.0.0.1:8000"

    assert snapshot.connectors == []
    assert snapshot.programs == fake_programs

    assert snapshot.flows.id == "flows"
    assert snapshot.flows.implemented is False

    assert snapshot.journal.id == "journal"
    assert snapshot.journal.implemented is False

    assert snapshot.agents.id == "agents"
    assert snapshot.agents.implemented is False


def test_settings_diagnostic_counts_programs_correctly(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
    configure_fake_environment(monkeypatch)
    configure_fake_dependencies(
        monkeypatch,
        fake_programs,
        empty_flows_registry,
        empty_journal_registry,
        empty_agents_registry,
    )

    snapshot = settings_service.build_settings_snapshot()

    assert snapshot.diagnostic.api_ok is True
    assert snapshot.diagnostic.connectors_total == 0
    assert snapshot.diagnostic.programs_total == 2
    assert snapshot.diagnostic.programs_available == 1


def test_settings_reports_configuration_without_exposing_values(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
    configure_fake_environment(monkeypatch)
    configure_fake_dependencies(
        monkeypatch,
        fake_programs,
        empty_flows_registry,
        empty_journal_registry,
        empty_agents_registry,
    )

    snapshot = settings_service.build_settings_snapshot()

    configuration = {item.id: item for item in snapshot.diagnostic.configuration}

    assert configuration["NOTION_TOKEN"].configured is True
    assert configuration["NOTION_TOKEN"].secret is True

    assert configuration["GITHUB_TOKEN"].configured is True
    assert configuration["GITHUB_TOKEN"].secret is True

    assert configuration["OPENAI_API_KEY"].configured is True
    assert configuration["OPENAI_API_KEY"].secret is True

    assert configuration["GOOGLE_CLIENT_ID"].configured is True
    assert configuration["GOOGLE_CLIENT_ID"].secret is True

    assert configuration["CHESS_COM_USERNAME"].configured is True
    assert configuration["CHESS_COM_USERNAME"].secret is False


def test_settings_serialization_never_contains_secret_values(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
    configure_fake_environment(monkeypatch)
    configure_fake_dependencies(
        monkeypatch,
        fake_programs,
        empty_flows_registry,
        empty_journal_registry,
        empty_agents_registry,
    )

    snapshot = settings_service.build_settings_snapshot()
    serialized = snapshot.model_dump_json()

    assert "secret-notion-token" not in serialized
    assert "secret-github-token" not in serialized
    assert "secret-openai-key" not in serialized
    assert "google-client-id" not in serialized

    assert "NOTION_TOKEN" in serialized
    assert "GITHUB_TOKEN" in serialized
    assert "OPENAI_API_KEY" in serialized


def test_settings_marks_missing_configuration_as_not_configured(
    monkeypatch: pytest.MonkeyPatch,
    fake_programs: list[dict[str, Any]],
    empty_flows_registry: RegistrySnapshot,
    empty_journal_registry: RegistrySnapshot,
    empty_agents_registry: RegistrySnapshot,
) -> None:
    configure_fake_environment(monkeypatch)
    configure_fake_dependencies(
        monkeypatch,
        fake_programs,
        empty_flows_registry,
        empty_journal_registry,
        empty_agents_registry,
    )

    monkeypatch.setattr(settings_service.env, "NOTION_TOKEN", None)
    monkeypatch.setattr(settings_service.env, "GITHUB_TOKEN", "")
    monkeypatch.setattr(settings_service.env, "OPENAI_API_KEY", None)

    snapshot = settings_service.build_settings_snapshot()

    configuration = {item.id: item for item in snapshot.diagnostic.configuration}

    assert configuration["NOTION_TOKEN"].configured is False
    assert configuration["GITHUB_TOKEN"].configured is False
    assert configuration["OPENAI_API_KEY"].configured is False
