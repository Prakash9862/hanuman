from __future__ import annotations

from pathlib import Path

import pytest

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


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("invalid", None),
        ("2026-01-01T12:00:00", "2026-01-01T12:00:00+00:00"),
        ("2026-01-01T13:00:00+01:00", "2026-01-01T12:00:00+00:00"),
    ],
)
def test_parse_datetime_normalizes_utc(value, expected):
    parsed = dashboard._parse_datetime(value)
    assert (parsed.isoformat() if parsed else None) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("body", {}),
        ("---\nmissing end", {}),
        ("---\n[invalid\n---\nbody", {}),
        ("---\n- list\n---\nbody", {}),
        ("---\ntitle: Note\ntags: a, b\n---\nbody", {"title": "Note", "tags": "a, b"}),
    ],
)
def test_frontmatter_handles_supported_and_invalid_documents(text, expected):
    assert dashboard._frontmatter(text) == expected


def test_tags_accepts_lists_strings_and_rejects_other_values():
    assert dashboard._tags([" one ", "", 2]) == ["one", "2"]
    assert dashboard._tags("one, two, ") == ["one", "two"]
    assert dashboard._tags(42) == []


def test_vault_path_validates_environment(tmp_path: Path, monkeypatch):
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("OBSIDIAN_VAULT_DIR", raising=False)
    with pytest.raises(RuntimeError, match="OBSIDIAN_VAULT_PATH"):
        dashboard._vault_path()

    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing"))
    with pytest.raises(FileNotFoundError, match="introuvable"):
        dashboard._vault_path()

    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    assert dashboard._vault_path() == tmp_path


def test_scan_obsidian_notes_filters_hidden_and_query(tmp_path: Path, monkeypatch):
    (tmp_path / "Zulu.md").write_text(
        "---\ntitle: Zulu\ntags: music, opera\nnotion_page_id: page\n"
        "notion_last_sync: 2026-01-01T00:00:00Z\n---\nBody",
        encoding="utf-8",
    )
    (tmp_path / "Alpha.md").write_text("# Alpha", encoding="utf-8")
    hidden = tmp_path / ".obsidian"
    hidden.mkdir()
    (hidden / "ignored.md").write_text("# ignored", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    monkeypatch.setenv("OBSIDIAN_VAULT_NAME", "My Vault")

    notes = dashboard.scan_obsidian_notes("opera")

    assert [note["title"] for note in notes] == ["Zulu"]
    assert notes[0]["tags"] == ["music", "opera"]
    assert notes[0]["notion_page_id"] == "page"
    assert "vault=My%20Vault" in notes[0]["open_url"]
    assert [note["title"] for note in dashboard.scan_obsidian_notes()] == [
        "Alpha",
        "Zulu",
    ]


def test_scan_obsidian_notes_skips_unreadable_note(tmp_path: Path, monkeypatch):
    note = tmp_path / "bad.md"
    note.write_bytes(b"\xff")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))
    assert dashboard.scan_obsidian_notes() == []


def test_scan_notion_pages_paginates_filters_and_ignores_other_blocks(monkeypatch):
    requests = []

    class FakeService:
        def _request(self, method, path):
            requests.append(path)
            if len(requests) == 1:
                return {
                    "results": [
                        {"type": "paragraph", "id": "ignored"},
                        {
                            "type": "child_page",
                            "id": "page-1",
                            "child_page": {"title": "Architecture"},
                        },
                    ],
                    "has_more": True,
                    "next_cursor": "next cursor",
                }
            return {
                "results": [
                    {
                        "type": "child_page",
                        "id": "page-2",
                        "child_page": {"title": "Other"},
                    }
                ],
                "has_more": False,
            }

        def retrieve_page(self, page_id):
            return {
                "last_edited_time": "2026-01-01T00:00:00Z",
                "url": f"https://notion.test/{page_id}",
            }

    monkeypatch.setenv("NOTION_OBSIDIAN_PARENT_ID", "parent")
    monkeypatch.setattr(dashboard, "NotionService", FakeService)

    pages = dashboard.scan_notion_pages("architecture")

    assert [page["page_id"] for page in pages] == ["page-1"]
    assert "start_cursor=next%20cursor" in requests[1]


def test_scan_notion_pages_requires_parent_and_stops_on_missing_cursor(monkeypatch):
    for key in ("NOTION_OBSIDIAN_PARENT_ID", "NOTION_PARENT_PAGE_ID", "NOTION_PARENT_ID"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="NOTION_OBSIDIAN_PARENT_ID"):
        dashboard.scan_notion_pages()

    class FakeService:
        def _request(self, method, path):
            return {"results": [], "has_more": True, "next_cursor": None}

    monkeypatch.setenv("NOTION_PARENT_ID", "parent")
    monkeypatch.setattr(dashboard, "NotionService", FakeService)
    assert dashboard.scan_notion_pages() == []


@pytest.mark.parametrize(
    ("note_time", "notion_time", "expected"),
    [
        ("2026-01-02T00:00:00Z", "2026-01-01T00:00:00Z", SyncStatus.OBSIDIAN_NEWER),
        ("2026-01-01T00:00:00Z", "2026-01-02T00:00:00Z", SyncStatus.NOTION_NEWER),
    ],
)
def test_linked_status_distinguishes_change_source(note_time, notion_time, expected):
    assert (
        dashboard._linked_status(
            {"last_sync_at": "2026-01-01T12:00:00Z", "modified_at": note_time},
            {"modified_at": notion_time},
        )
        == expected
    )


def test_linked_status_is_unknown_without_last_sync():
    assert dashboard._linked_status({"last_sync_at": None}, {}) == SyncStatus.UNKNOWN
