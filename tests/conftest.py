from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Generator

import pytest
from fastapi.testclient import TestClient

from hanuman.main import app


def _ensure_src_on_path() -> None:
    """Ensure the project ``src`` directory is importable during tests.

    The CI executes the suite without installing the package, so we extend
    ``sys.path`` manually to point to ``src`` in order to import ``hanuman``.
    This keeps the behaviour consistent with ``poetry install`` while staying
    lightweight for local executions.
    """

    project_root = Path(__file__).resolve().parents[1]
    src_dir = project_root / "src"
    src_str = str(src_dir)
    if src_dir.exists() and src_str not in sys.path:
        sys.path.insert(0, src_str)


_ensure_src_on_path()


def _set_default_env_if_missing(key: str, value: str) -> None:
    os.environ.setdefault(key, value)


# Valeurs par défaut pour éviter les NOTION_* manquants en test
_DEFAULT_ENV_VARS: dict[str, str] = {
    "NOTION_TOKEN": "test-notion-token",
    "NOTION_VERSION": "2025-09-03",
    "GITHUB_TOKEN": "test-github-token",
    "OPENAI_API_KEY": "test-openai-key",
    "GOOGLE_CLIENT_ID": "test-google-client-id",
    "GOOGLE_CLIENT_SECRET": "test-google-client-secret",
    "GOOGLE_REDIRECT_URI": "https://example.com/oauth",
}

for env_key, env_value in _DEFAULT_ENV_VARS.items():
    _set_default_env_if_missing(env_key, env_value)


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c
