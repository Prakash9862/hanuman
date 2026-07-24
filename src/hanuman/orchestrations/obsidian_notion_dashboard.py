from __future__ import annotations

import hashlib
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import yaml

from hanuman.models.obsidian_notion import (
    NotionResource,
    ObsidianNotionItem,
    ObsidianNotionStats,
    ObsidianResource,
    SyncStatus,
)
from hanuman.services.core.notion_service import NotionService

_EXCLUDED_DIRS = {".git", ".obsidian", ".trash", "node_modules"}


def _parse_datetime(value: Any) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _frontmatter(text: str) -> dict[str, Any]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}
    try:
        loaded = yaml.safe_load(text[4:end]) or {}
    except yaml.YAMLError:
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _tags(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return []


def _vault_path() -> Path:
    raw = os.getenv("OBSIDIAN_VAULT_PATH") or os.getenv("OBSIDIAN_VAULT_DIR")
    if not raw:
        raise RuntimeError("OBSIDIAN_VAULT_PATH manquant dans l'environnement")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        raise FileNotFoundError(f"Vault Obsidian introuvable: {vault}")
    return vault


def _obsidian_url(vault: Path, relative_path: str) -> str:
    vault_name = os.getenv("OBSIDIAN_VAULT_NAME") or vault.name
    file_without_suffix = str(Path(relative_path).with_suffix(""))
    return f"obsidian://open?vault={quote(vault_name)}&file={quote(file_without_suffix)}"


def scan_obsidian_notes(query: str | None = None) -> list[dict[str, Any]]:
    vault = _vault_path()
    needle = (query or "").strip().casefold()
    notes: list[dict[str, Any]] = []

    for path in vault.rglob("*.md"):
        relative = path.relative_to(vault)
        if any(part.startswith(".") or part in _EXCLUDED_DIRS for part in relative.parts[:-1]):
            continue
        try:
            text = path.read_text(encoding="utf-8")
            metadata = _frontmatter(text)
            stat = path.stat()
        except (OSError, UnicodeError):
            continue

        title = str(metadata.get("title") or path.stem)
        searchable = (
            f"{relative.as_posix()} {title} {' '.join(_tags(metadata.get('tags')))}".casefold()
        )
        if needle and needle not in searchable:
            continue

        notes.append(
            {
                "path": relative.as_posix(),
                "title": title,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
                "tags": _tags(metadata.get("tags")),
                "notion_page_id": str(metadata.get("notion_page_id") or "").strip() or None,
                "last_sync_at": metadata.get("notion_last_sync") or metadata.get("last_synced_at"),
                "open_url": _obsidian_url(vault, relative.as_posix()),
            }
        )

    return sorted(notes, key=lambda item: (item["title"].casefold(), item["path"].casefold()))


def scan_notion_pages(query: str | None = None) -> list[dict[str, Any]]:
    parent_id = (
        os.getenv("NOTION_OBSIDIAN_PARENT_ID")
        or os.getenv("NOTION_PARENT_PAGE_ID")
        or os.getenv("NOTION_PARENT_ID")
        or ""
    ).strip()
    if not parent_id:
        raise RuntimeError("NOTION_OBSIDIAN_PARENT_ID manquant dans l'environnement")

    service = NotionService()
    needle = (query or "").strip().casefold()
    pages: list[dict[str, Any]] = []
    cursor: str | None = None

    while True:
        suffix = "?page_size=100"
        if cursor:
            suffix += f"&start_cursor={quote(cursor)}"
        payload = service._request("GET", f"blocks/{parent_id}/children{suffix}")

        for block in payload.get("results", []):
            if block.get("type") != "child_page":
                continue
            page_id = str(block.get("id") or "").strip()
            title = str(block.get("child_page", {}).get("title") or "Page Notion")
            if needle and needle not in title.casefold():
                continue
            page = service.retrieve_page(page_id)
            pages.append(
                {
                    "page_id": page_id,
                    "title": title,
                    "modified_at": page.get("last_edited_time"),
                    "url": str(page.get("url") or ""),
                }
            )

        if not payload.get("has_more"):
            break
        cursor = payload.get("next_cursor")
        if not cursor:
            break

    return sorted(pages, key=lambda item: item["title"].casefold())


def _linked_status(note: dict[str, Any], page: dict[str, Any]) -> SyncStatus:
    last_sync = _parse_datetime(note.get("last_sync_at"))
    if last_sync is None:
        return SyncStatus.UNKNOWN

    obsidian_modified = _parse_datetime(note.get("modified_at"))
    notion_modified = _parse_datetime(page.get("modified_at"))
    obsidian_changed = bool(obsidian_modified and obsidian_modified > last_sync)
    notion_changed = bool(notion_modified and notion_modified > last_sync)

    if obsidian_changed and notion_changed:
        return SyncStatus.CONFLICT
    if obsidian_changed:
        return SyncStatus.OBSIDIAN_NEWER
    if notion_changed:
        return SyncStatus.NOTION_NEWER
    return SyncStatus.SYNCED


def build_items(query: str | None = None) -> list[ObsidianNotionItem]:
    notes = scan_obsidian_notes(query)
    pages = scan_notion_pages(query)
    pages_by_id = {page["page_id"]: page for page in pages}
    linked_page_ids: set[str] = set()
    items: list[ObsidianNotionItem] = []

    for note in notes:
        page_id = note.get("notion_page_id")
        page = pages_by_id.get(page_id) if page_id else None
        if page:
            linked_page_ids.add(page["page_id"])
            status = _linked_status(note, page)
        else:
            status = SyncStatus.OBSIDIAN_ONLY

        stable_id = hashlib.sha1(note["path"].encode("utf-8")).hexdigest()[:16]
        items.append(
            ObsidianNotionItem(
                id=f"obsidian:{stable_id}",
                title=note["title"],
                status=status,
                obsidian=ObsidianResource(
                    path=note["path"],
                    title=note["title"],
                    modified_at=note["modified_at"],
                    tags=note["tags"],
                    open_url=note["open_url"],
                ),
                notion=(
                    NotionResource(
                        page_id=page["page_id"],
                        title=page["title"],
                        modified_at=page.get("modified_at"),
                        url=page["url"],
                    )
                    if page
                    else None
                ),
            )
        )

    for page in pages:
        if page["page_id"] in linked_page_ids:
            continue
        items.append(
            ObsidianNotionItem(
                id=f"notion:{page['page_id']}",
                title=page["title"],
                status=SyncStatus.NOTION_ONLY,
                notion=NotionResource(
                    page_id=page["page_id"],
                    title=page["title"],
                    modified_at=page.get("modified_at"),
                    url=page["url"],
                ),
            )
        )

    return sorted(items, key=lambda item: (item.title.casefold(), item.id))


def build_stats(items: list[ObsidianNotionItem]) -> ObsidianNotionStats:
    counts = {status: 0 for status in SyncStatus}
    for item in items:
        counts[item.status] += 1

    return ObsidianNotionStats(
        vault_notes=sum(item.obsidian is not None for item in items),
        notion_pages=sum(item.notion is not None for item in items),
        linked=sum(item.obsidian is not None and item.notion is not None for item in items),
        synced=counts[SyncStatus.SYNCED],
        obsidian_only=counts[SyncStatus.OBSIDIAN_ONLY],
        notion_only=counts[SyncStatus.NOTION_ONLY],
        obsidian_newer=counts[SyncStatus.OBSIDIAN_NEWER],
        notion_newer=counts[SyncStatus.NOTION_NEWER],
        conflicts=counts[SyncStatus.CONFLICT],
    )
