from __future__ import annotations

from hanuman.config import env
from hanuman.models.settings import (
    ConfigurationItem,
    DiagnosticSnapshot,
    GeneralSettingsSnapshot,
    SettingsSnapshot,
)
from hanuman.services.agents_registry import get_agents_registry
from hanuman.services.connectors_registry import list_connectors
from hanuman.services.flows_registry import get_flows_registry
from hanuman.services.journal_registry import get_journal_registry
from hanuman.services.local_programs_service import inspect_programs


def _is_configured(value: object) -> bool:
    if value is None:
        return False

    if isinstance(value, str):
        return value.strip().lower() not in {"", "null", "none"}

    return True


def _configuration_snapshot() -> list[ConfigurationItem]:
    return [
        ConfigurationItem(
            id="NOTION_TOKEN",
            configured=_is_configured(env.NOTION_TOKEN),
            secret=True,
        ),
        ConfigurationItem(
            id="GITHUB_TOKEN",
            configured=_is_configured(env.GITHUB_TOKEN),
            secret=True,
        ),
        ConfigurationItem(
            id="OPENAI_API_KEY",
            configured=_is_configured(env.OPENAI_API_KEY),
            secret=True,
        ),
        ConfigurationItem(
            id="GOOGLE_CLIENT_ID",
            configured=_is_configured(env.GOOGLE_CLIENT_ID),
            secret=True,
        ),
        ConfigurationItem(
            id="GOOGLE_CLIENT_SECRET",
            configured=_is_configured(env.GOOGLE_CLIENT_SECRET),
            secret=True,
        ),
        ConfigurationItem(
            id="GOOGLE_REDIRECT_URI",
            configured=_is_configured(env.GOOGLE_REDIRECT_URI),
            secret=False,
        ),
        ConfigurationItem(
            id="CHESS_COM_USERNAME",
            configured=_is_configured(env.CHESS_COM_USERNAME),
            secret=False,
        ),
    ]


def build_settings_snapshot() -> SettingsSnapshot:
    connectors = list_connectors()
    programs = inspect_programs()

    programs_available = sum(1 for program in programs if program.get("installed") is True)

    return SettingsSnapshot(
        general=GeneralSettingsSnapshot(
            app_env=env.APP_ENV,
            log_level=env.LOG_LEVEL,
            api_base_url=env.BASE_URL,
        ),
        connectors=connectors,
        programs=programs,
        flows=get_flows_registry(),
        journal=get_journal_registry(),
        agents=get_agents_registry(),
        diagnostic=DiagnosticSnapshot(
            api_ok=True,
            connectors_total=len(connectors),
            programs_total=len(programs),
            programs_available=programs_available,
            configuration=_configuration_snapshot(),
        ),
        about={
            "name": "Hanuman",
            "version": "v5-dev",
        },
    )
