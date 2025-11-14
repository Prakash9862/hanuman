from __future__ import annotations

import os
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from hanuman.main import app


def _set_default_env_if_missing(key: str, value: str) -> None:
    os.environ.setdefault(key, value)


# Valeurs par défaut pour éviter les NOTION_* manquants en test
_DEFAULT_ENV_VARS: dict[str, str] = {
    "NOTION_TOKEN": "test-notion-token",
    "NOTION_VERSION": "2025-09-03",
}

for env_key, env_value in _DEFAULT_ENV_VARS.items():
    _set_default_env_if_missing(env_key, env_value)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
