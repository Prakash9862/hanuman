from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from hanuman.api.routers import orchestrations


def test_resolve_relative_markdown_inside_vault(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    note = tmp_path / "folder" / "note.md"
    note.parent.mkdir()
    note.write_text("# Note", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path))

    assert orchestrations._resolve_obsidian_markdown_path("folder/note.md") == note


def test_resolve_absolute_markdown_without_vault(tmp_path: Path) -> None:
    note = tmp_path / "note.MD"
    note.write_text("# Note", encoding="utf-8")
    assert orchestrations._resolve_obsidian_markdown_path(str(note)) == note


def test_resolve_relative_path_requires_vault(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("OBSIDIAN_VAULT_PATH", raising=False)
    monkeypatch.delenv("OBSIDIAN_VAULT_DIR", raising=False)
    with pytest.raises(RuntimeError, match="OBSIDIAN_VAULT_PATH"):
        orchestrations._resolve_obsidian_markdown_path("note.md")


def test_resolve_rejects_traversal_missing_file_and_non_markdown(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()
    (tmp_path / "outside.md").write_text("outside", encoding="utf-8")
    (vault / "note.txt").write_text("text", encoding="utf-8")
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(vault))

    with pytest.raises(ValueError, match="hors du vault"):
        orchestrations._resolve_obsidian_markdown_path("../outside.md")
    with pytest.raises(FileNotFoundError, match="introuvable"):
        orchestrations._resolve_obsidian_markdown_path("missing.md")
    with pytest.raises(ValueError, match="Markdown"):
        orchestrations._resolve_obsidian_markdown_path("note.txt")


def test_dashboard_items_and_stats_return_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(orchestrations, "build_items", lambda query=None: [])
    expected_stats = orchestrations.ObsidianNotionStats(
        vault_notes=0,
        notion_pages=0,
        linked=0,
        synced=0,
        obsidian_only=0,
        notion_only=0,
        obsidian_newer=0,
        notion_newer=0,
        conflicts=0,
    )
    monkeypatch.setattr(orchestrations, "build_stats", lambda items: expected_stats)

    assert orchestrations.obsidian_notion_items("query").total == 0
    assert orchestrations.obsidian_notion_stats() is expected_stats


@pytest.mark.parametrize("endpoint", ["items", "stats"])
def test_dashboard_maps_failures(monkeypatch: pytest.MonkeyPatch, endpoint: str) -> None:
    monkeypatch.setattr(
        orchestrations,
        "build_items",
        lambda *args: (_ for _ in ()).throw(RuntimeError("vault broken")),
    )

    with pytest.raises(HTTPException) as caught:
        if endpoint == "items":
            orchestrations.obsidian_notion_items()
        else:
            orchestrations.obsidian_notion_stats()

    assert caught.value.status_code == 502


def test_obsidian_publish_requires_parent(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "NOTION_OBSIDIAN_PARENT_ID",
        "NOTION_PARENT_PAGE_ID",
        "NOTION_PARENT_ID",
    ):
        monkeypatch.delenv(key, raising=False)

    with pytest.raises(HTTPException) as caught:
        orchestrations.obsidian_to_notion(orchestrations.ObsidianToNotionIn(path="note.md"))

    assert caught.value.status_code == 400


def test_obsidian_publish_uses_environment_defaults(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    note = tmp_path / "note.md"
    note.write_text("# Note", encoding="utf-8")
    captured: dict[str, object] = {}
    monkeypatch.setenv("NOTION_OBSIDIAN_PARENT_ID", "parent")
    monkeypatch.setenv("NOTION_DB_TITLE_NAME", "Title")
    monkeypatch.setattr(
        orchestrations,
        "send_markdown_to_notion_safe",
        lambda **kwargs: captured.update(kwargs) or {"id": "page"},
    )

    result = orchestrations.obsidian_to_notion(orchestrations.ObsidianToNotionIn(path=str(note)))

    assert result == {"ok": True, "notion": {"id": "page"}}
    assert captured["parent_id"] == "parent"
    assert captured["db_title_name"] == "Title"


@pytest.mark.parametrize(
    ("error", "status"),
    [(ValueError("bad path"), 400), (RuntimeError("notion down"), 502)],
)
def test_obsidian_publish_maps_failures(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    error: Exception,
    status: int,
) -> None:
    note = tmp_path / "note.md"
    note.write_text("# Note", encoding="utf-8")
    monkeypatch.setattr(
        orchestrations,
        "send_markdown_to_notion_safe",
        lambda **kwargs: (_ for _ in ()).throw(error),
    )

    with pytest.raises(HTTPException) as caught:
        orchestrations.obsidian_to_notion(
            orchestrations.ObsidianToNotionIn(path=str(note), parent_id="parent")
        )

    assert caught.value.status_code == status


def test_wikipedia_publish_handles_missing_parent_success_and_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    for key in (
        "NOTION_WIKIPEDIA_PARENT_ID",
        "NOTION_PARENT_PAGE_ID",
        "NOTION_PARENT_ID",
    ):
        monkeypatch.delenv(key, raising=False)
    body = orchestrations.WikipediaToNotionIn(query="Ada Lovelace")
    assert orchestrations.wikipedia_to_notion(body)["ok"] is False

    monkeypatch.setattr(
        orchestrations,
        "publish_wikipedia_page_to_notion",
        lambda *args, **kwargs: SimpleNamespace(page_id="page", url="https://notion.test"),
    )
    success = orchestrations.wikipedia_to_notion(
        orchestrations.WikipediaToNotionIn(query="Ada", parent_id="parent")
    )
    assert success["notion"] == {"id": "page", "url": "https://notion.test"}

    monkeypatch.setattr(
        orchestrations,
        "publish_wikipedia_page_to_notion",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")),
    )
    assert orchestrations.wikipedia_to_notion(
        orchestrations.WikipediaToNotionIn(query="Ada", parent_id="parent")
    ) == {"ok": False, "error": "offline"}


def test_orchestration_ping_contract() -> None:
    assert orchestrations.orchestration_ping() == {
        "status": "ok",
        "module": "orchestrations",
    }
