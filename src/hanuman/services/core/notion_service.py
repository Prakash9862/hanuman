# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import requests

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")
NOTION_VERSION = os.getenv("NOTION_VERSION", "2025-09-03")
DEFAULT_PARENT = os.getenv("NOTION_PARENT_ID", "")  # page_id (UUID avec tirets)
API = "https://api.notion.com/v1"


def _hdr() -> Dict[str, str]:
    if not NOTION_TOKEN:
        raise RuntimeError("NOTION_TOKEN manquant.")
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def create_page_under_parent(
    title: str, blocks: List[Dict[str, Any]], parent_page_id: str | None = None
) -> Dict[str, Any]:
    parent = (parent_page_id or DEFAULT_PARENT).strip()
    if not parent:
        raise RuntimeError("NOTION_PARENT_ID manquant (env ou param).")
    payload: Dict[str, Any] = {
        "parent": {"page_id": parent},
        "properties": {"title": {"title": [{"type": "text", "text": {"content": title}}]}},
    }
    if blocks:
        payload["children"] = blocks[:95]  # marge de sécurité
    r = requests.post(f"{API}/pages", headers=_hdr(), data=json.dumps(payload), timeout=30)
    if r.status_code >= 300:
        raise RuntimeError(f"Notion error {r.status_code}: {r.text}")
    return r.json()
