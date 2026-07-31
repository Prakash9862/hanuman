from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class RegistryState(StrEnum):
    AVAILABLE = "available"
    EMPTY = "empty"
    NOT_IMPLEMENTED = "not_implemented"


class RegistrySnapshot(BaseModel):
    id: str
    label: str
    state: RegistryState
    implemented: bool
    entries: list[dict[str, Any]] = Field(default_factory=list)
    message: str | None = None
