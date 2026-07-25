from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ConnectorKind(StrEnum):
    REMOTE_API = "remote_api"
    LOCAL_FILESYSTEM = "local_filesystem"
    LOCAL_PROGRAM = "local_program"
    AI_PROVIDER = "ai_provider"


class ConnectorState(StrEnum):
    REGISTERED = "registered"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    DOWN = "down"
    NOT_CONFIGURED = "not_configured"


class ConnectorDescriptor(BaseModel):
    id: str
    label: str
    description: str
    kind: ConnectorKind
    capabilities: list[str] = Field(default_factory=list)
    writable: bool = False
    requires_auth: bool = False
    status_endpoint: str | None = None
    state: ConnectorState = ConnectorState.REGISTERED


class ConnectorList(BaseModel):
    connectors: list[ConnectorDescriptor]
    total: int


class CapabilityProvider(BaseModel):
    capability: str
    connector_ids: list[str]


class CapabilityList(BaseModel):
    capabilities: list[CapabilityProvider]
    total: int
