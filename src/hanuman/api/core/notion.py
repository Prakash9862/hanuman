# src/hanuman/api/core/notion.py
import os

import requests
from fastapi import APIRouter

router = APIRouter(prefix="/notion", tags=["notion"])

NOTION_API = "https://api.notion.com/v1"


def _headers() -> dict:
    token = os.getenv("NOTION_TOKEN", "")
    version = os.getenv("NOTION_VERSION", "2025-09-03")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": version,
        "Content-Type": "application/json",
    }


@router.get("/ping")
def ping():
    token = os.getenv("NOTION_TOKEN", "")
    if not token:
        return {"ok": False, "error": "Missing NOTION_TOKEN in environment"}

    try:
        r = requests.get(f"{NOTION_API}/users/me", headers=_headers(), timeout=10)
        if r.status_code == 200:
            js = r.json()
            ws = (js.get("bot") or {}).get("workspace")
            return {"ok": True, "workspace": ws, "status": r.status_code}
        return {"ok": False, "status": r.status_code, "body": r.text[:3000]}
    except Exception as e:
        return {"ok": False, "error": str(e)}
