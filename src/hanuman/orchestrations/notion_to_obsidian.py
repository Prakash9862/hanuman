from __future__ import annotations

import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, cast

import yaml

from hanuman.services.core.obsidian_service import ObsidianService


def _notion_headers() -> dict[str, str]:
    token = os.environ.get("NOTION_TOKEN")
    if not token:
        raise RuntimeError("NOTION_TOKEN manquant dans l'environnement")
    return {
        "Authorization": f"Bearer {token}",
        "Notion-Version": os.environ.get("NOTION_VERSION", "2025-09-03"),
        "Content-Type": "application/json",
    }


def _get_json(url: str) -> dict[str, Any]:
    request = urllib.request.Request(url=url, headers=_notion_headers(), method="GET")
    with urllib.request.urlopen(request, timeout=30) as response:
        return cast(dict[str, Any], json.loads(response.read().decode("utf-8")))


def _plain_text(rich_text: list[dict[str, Any]]) -> str:
    return "".join(str(item.get("plain_text") or item.get("text", {}).get("content") or "") for item in rich_text)


def _page_title(page: dict[str, Any]) -> str:
    properties = page.get("properties", {})
    for property_value in properties.values():
        if isinstance(property_value, dict) and property_value.get("type") == "title":
            title = _plain_text(property_value.get("title", []))
            if title:
                return title
    return "Page Notion"


def _block_to_markdown(block: dict[str, Any]) -> str:
    block_type = block.get("type")
    data = block.get(block_type, {}) if isinstance(block_type, str) else {}
    text = _plain_text(data.get("rich_text", []))

    if block_type == "paragraph":
        return text
    if block_type == "heading_1":
        return f"# {text}"
    if block_type == "heading_2":
        return f"## {text}"
    if block_type == "heading_3":
        return f"### {text}"
    if block_type == "bulleted_list_item":
        return f"- {text}"
    if block_type == "numbered_list_item":
        return f"1. {text}"
    if block_type == "quote":
        return f"> {text}"
    if block_type == "code":
        language = data.get("language") or ""
        return f"```{language}\n{text}\n```"
    if block_type == "divider":
        return "---"
    if block_type == "callout":
        return f"> {text}"
    return text


def notion_blocks_to_markdown(blocks: list[dict[str, Any]]) -> str:
    return "\n\n".join(part for part in (_block_to_markdown(block) for block in blocks) if part).strip()


def _safe_filename(title: str) -> str:
    cleaned = re.sub(r"[\\/:*?\"<>|]", "-", title).strip().strip(".")
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned or "Page Notion"


def read_notion_page(page_id: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    page = _get_json(f"https://api.notion.com/v1/pages/{urllib.parse.quote(page_id)}")
    blocks: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        query = "?page_size=100"
        if cursor:
            query += "&start_cursor=" + urllib.parse.quote(cursor)
        payload = _get_json(
            f"https://api.notion.com/v1/blocks/{urllib.parse.quote(page_id)}/children{query}"
        )
        blocks.extend(payload.get("results", []))
        if not payload.get("has_more"):
            break
        cursor = payload.get("next_cursor")
        if not cursor:
            break

    return page, blocks


def import_notion_page_to_obsidian(
    page_id: str,
    *,
    destination_dir: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    page, blocks = read_notion_page(page_id)
    title = _page_title(page)
    body = notion_blocks_to_markdown(blocks)
    destination = destination_dir or os.environ.get("OBSIDIAN_NOTION_IMPORT_DIR", "Notion")
    relative_path = Path(destination) / f"{_safe_filename(title)}.md"

    frontmatter = {
        "title": title,
        "notion_page_id": page_id,
        "notion_url": page.get("url"),
        "notion_last_edited_time": page.get("last_edited_time"),
    }
    markdown = f"---\n{yaml.safe_dump(frontmatter, allow_unicode=True, sort_keys=False)}---\n\n{body}\n"

    note_path = ObsidianService().write_note(relative_path, markdown, overwrite=overwrite)
    return {
        "status": "imported",
        "notion_page_id": page_id,
        "notion_url": page.get("url"),
        "note_path": note_path,
        "created": not overwrite,
    }
