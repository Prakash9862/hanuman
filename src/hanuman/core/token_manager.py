# src/hanuman/core/token_manager.py

import json
from pathlib import Path

TOKEN_DIR = Path("secrets")
TOKEN_DIR.mkdir(exist_ok=True)


def save_token_json(service: str, data: dict):
    filepath = TOKEN_DIR / f"{service}_token.json"
    with filepath.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_token_json(service: str) -> dict:
    filepath = TOKEN_DIR / f"{service}_token.json"
    if not filepath.exists():
        return {}
    with filepath.open(encoding="utf-8") as f:
        return json.load(f)
