from __future__ import annotations

from hanuman.models.obsidian_notion import SyncStatus
from hanuman.orchestrations import obsidian_notion_dashboard as dashboard


def test_build_items_links_frontmatter_page(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "scan_obsidian_notes",
        lambda query=None: [
            {
                "path": "Hanuman/Architecture.md",
                "title": "Architecture Hanuman",
                "modified_at": "2026-07-24T10:00:00+00:00",
                "tags": ["hanuman"],
                "notion_page_id": "page-1",
                "last_sync_at": "2026-07-24T10:00:00+00:00",
                "open_url": "obsidian://open?vault=Vault&file=Hanuman%2FArchitecture",
            }
        ],
    )
    monkeypatch.setattr(
        dashboard,
        "scan_notion_pages",
        lambda query=None: [
            {
                "page_id": "page-1",
                "title": "Architecture Hanuman",
                "modified_at": "2026-07-24T10:00:00+00:00",
                "url": "https://www.notion.so/page-1",
            }
        ],
    )

    items = dashboard.build_items()

    assert len(items) == 1
    assert items[0].status == SyncStatus.SYNCED
    assert items[0].obsidian is not None
    assert items[0].notion is not None


def test_build_items_marks_conflict(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "scan_obsidian_notes",
        lambda query=None: [
            {
                "path": "Note.md",
                "title": "Note",
                "modified_at": "2026-07-24T12:00:00+00:00",
                "tags": [],
                "notion_page_id": "page-1",
                "last_sync_at": "2026-07-24T10:00:00+00:00",
                "open_url": "obsidian://open?vault=Vault&file=Note",
            }
        ],
    )
    monkeypatch.setattr(
        dashboard,
        "scan_notion_pages",
        lambda query=None: [
            {
                "page_id": "page-1",
                "title": "Note",
                "modified_at": "2026-07-24T11:00:00+00:00",
                "url": "https://www.notion.so/page-1",
            }
        ],
    )

    assert dashboard.build_items()[0].status == SyncStatus.CONFLICT


def test_build_stats_counts_both_sides(monkeypatch):
    monkeypatch.setattr(
        dashboard,
        "scan_obsidian_notes",
        lambda query=None: [
            {
                "path": "Local.md",
                "title": "Local",
                "modified_at": "2026-07-24T10:00:00+00:00",
                "tags": [],
                "notion_page_id": None,
                "last_sync_at": None,
                "open_url": "obsidian://open?vault=Vault&file=Local",
            }
        ],
    )
    monkeypatch.setattr(
        dashboard,
        "scan_notion_pages",
        lambda query=None: [
            {
                "page_id": "page-2",
                "title": "Distant",
                "modified_at": "2026-07-24T10:00:00+00:00",
                "url": "https://www.notion.so/page-2",
            }
        ],
    )

    stats = dashboard.build_stats(dashboard.build_items())

    assert stats.vault_notes == 1
    assert stats.notion_pages == 1
    assert stats.obsidian_only == 1
    assert stats.notion_only == 1
    assert stats.linked == 0
