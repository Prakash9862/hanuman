from __future__ import annotations

import json
from pathlib import Path

from hanuman.core import token_manager


def test_save_and_load_token_json(tmp_path: Path, monkeypatch) -> None:
    storage_dir = tmp_path / "secrets"
    storage_dir.mkdir()
    monkeypatch.setattr(token_manager, "TOKEN_DIR", storage_dir)

    payload = {"access_token": "abc", "refresh_token": "def"}

    token_manager.save_token_json("notion", payload)

    saved_file = storage_dir / "notion_token.json"
    assert saved_file.exists()
    assert json.loads(saved_file.read_text(encoding="utf-8")) == payload

    loaded = token_manager.load_token_json("notion")
    assert loaded == payload


def test_load_token_json_missing_file(tmp_path: Path, monkeypatch) -> None:
    storage_dir = tmp_path / "secrets"
    storage_dir.mkdir()
    monkeypatch.setattr(token_manager, "TOKEN_DIR", storage_dir)

    assert token_manager.load_token_json("missing") == {}
