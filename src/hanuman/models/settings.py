from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from hanuman.models.connectors import ConnectorDescriptor
from hanuman.models.registry import RegistrySnapshot


class GeneralSettingsSnapshot(BaseModel):
    app_env: str
    log_level: str
    api_base_url: str


class ConfigurationItem(BaseModel):
    id: str
    configured: bool
    secret: bool = False
    message: str | None = None


class DiagnosticSnapshot(BaseModel):
    api_ok: bool
    connectors_total: int
    programs_total: int
    programs_available: int
    configuration: list[ConfigurationItem] = Field(default_factory=list)


class SettingsSnapshot(BaseModel):
    general: GeneralSettingsSnapshot
    connectors: list[ConnectorDescriptor] = Field(default_factory=list)
    programs: list[dict[str, Any]] = Field(default_factory=list)
    flows: RegistrySnapshot
    journal: RegistrySnapshot
    agents: RegistrySnapshot
    diagnostic: DiagnosticSnapshot
    about: dict[str, str] = Field(default_factory=dict)
