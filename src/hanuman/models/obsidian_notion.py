from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class SyncStatus(StrEnum):
    SYNCED = "synced"
    OBSIDIAN_ONLY = "obsidian_only"
    NOTION_ONLY = "notion_only"
    OBSIDIAN_NEWER = "obsidian_newer"
    NOTION_NEWER = "notion_newer"
    CONFLICT = "conflict"
    UNKNOWN = "unknown"


class ObsidianResource(BaseModel):
    path: str
    title: str
    modified_at: str
    tags: list[str] = Field(default_factory=list)
    open_url: str


class NotionResource(BaseModel):
    page_id: str
    title: str
    modified_at: str | None = None
    url: str


class ObsidianNotionItem(BaseModel):
    id: str
    title: str
    status: SyncStatus
    obsidian: ObsidianResource | None = None
    notion: NotionResource | None = None


class ObsidianNotionItemsResponse(BaseModel):
    items: list[ObsidianNotionItem]
    total: int


class ObsidianNotionStats(BaseModel):
    vault_notes: int
    notion_pages: int
    linked: int
    synced: int
    obsidian_only: int
    notion_only: int
    obsidian_newer: int
    notion_newer: int
    conflicts: int
