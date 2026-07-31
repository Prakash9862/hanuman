from __future__ import annotations

from fastapi import APIRouter

from hanuman.models.settings import SettingsSnapshot
from hanuman.services.settings_service import build_settings_snapshot

router = APIRouter(prefix="/settings", tags=["settings"])


@router.get("", response_model=SettingsSnapshot)
def get_settings() -> SettingsSnapshot:
    return build_settings_snapshot()
