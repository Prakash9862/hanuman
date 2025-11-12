import os
from typing import Any, Dict, cast

import requests

# ───────────────────────────────
# ENV
# ───────────────────────────────
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
NOTION_PARENT_ID = os.getenv("NOTION_PARENT_ID")
NOTION_TOKEN = os.getenv("NOTION_TOKEN")


# ───────────────────────────────
# ORCHESTRATION : GitHub → Notion
# ───────────────────────────────
def sync_github_to_notion(repo: str) -> Dict[str, Any]:
    """
    Synchronise un dépôt GitHub vers Notion.
    Crée une page Notion contenant les infos du repo (nom, description, stars...).
    """

    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    url = f"https://api.github.com/repos/{repo}"

    response = requests.get(url, headers=headers, timeout=10)
    if response.status_code != 200:
        return {
            "error": f"Impossible d’accéder au repo : {repo}",
            "status": response.status_code,
        }

    repo_data = response.json()
    repo_name = repo_data.get("name", "inconnu")
    repo_desc = repo_data.get("description", "Pas de description")
    stars = repo_data.get("stargazers_count", 0)
    forks = repo_data.get("forks_count", 0)
    url_html = repo_data.get("html_url", "")

    # ───── Notion page creation ─────
    payload: Dict[str, Any] = {
        "parent": {"type": "page_id", "page_id": NOTION_PARENT_ID},
        "properties": {
            "Name": {"title": [{"text": {"content": repo_name}}]},
            "Description": {"rich_text": [{"text": {"content": repo_desc}}]},
            "Stars": {"number": stars},
            "Forks": {"number": forks},
            "URL": {"url": url_html},
        },
    }

    notion_headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2025-09-03",
    }

    notion_response = requests.post(
        "https://api.notion.com/v1/pages",
        json=payload,
        headers=notion_headers,
        timeout=10,
    )

    if notion_response.status_code == 200:
        notion_data = cast(Dict[str, Any], notion_response.json())
        return {
            "status": "success",
            "repo": repo_name,
            "page_id": notion_data.get("id"),
        }
    else:
        return {
            "status": "error",
            "code": notion_response.status_code,
            "detail": notion_response.text,
        }
