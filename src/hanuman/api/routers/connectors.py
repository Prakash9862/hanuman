from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from hanuman.models.connectors import (
    CapabilityList,
    ConnectorDescriptor,
    ConnectorList,
)
from hanuman.services.connectors_registry import (
    get_connector,
    list_capabilities,
    list_connectors,
    providers_for,
)

router = APIRouter(prefix="/connectors", tags=["connectors"])


@router.get("", response_model=ConnectorList)
def connectors_list() -> ConnectorList:
    connectors = list_connectors()
    return ConnectorList(connectors=connectors, total=len(connectors))


@router.get("/capabilities", response_model=CapabilityList)
def capabilities_list() -> CapabilityList:
    capabilities = list_capabilities()
    return CapabilityList(capabilities=capabilities, total=len(capabilities))


@router.get("/providers", response_model=ConnectorList)
def capability_providers(
    capability: str = Query(min_length=1),
) -> ConnectorList:
    connectors = providers_for(capability)
    return ConnectorList(connectors=connectors, total=len(connectors))


@router.get("/{connector_id}", response_model=ConnectorDescriptor)
def connector_detail(connector_id: str) -> ConnectorDescriptor:
    connector = get_connector(connector_id)
    if connector is None:
        raise HTTPException(status_code=404, detail="Connecteur inconnu")
    return connector
