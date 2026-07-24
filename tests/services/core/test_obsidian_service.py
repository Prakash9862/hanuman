from pathlib import Path

import pytest

from hanuman.services.core.obsidian_service import ObsidianService


def test_list_notes_reads_frontmatter_and_ignores_hidden_dirs(tmp_path: Path) -> None:
    (tmp_path / "Projet").mkdir()
    (tmp_path / "Projet" / "Hanuman.md").write_text(
        "---\ntitle: Architecture Hanuman\ntags: [hanuman, notion]\n---\n\nContenu",
        encoding="utf-8",
    )
    (tmp_path / ".obsidian").mkdir()
    (tmp_path / ".obsidian" / "cache.md").write_text("secret", encoding="utf-8")

    notes = ObsidianService(tmp_path).list_notes()

    assert len(notes) == 1
    assert notes[0]["path"] == "Projet/Hanuman.md"
    assert notes[0]["title"] == "Architecture Hanuman"
    assert notes[0]["tags"] == ["hanuman", "notion"]


def test_read_note_rejects_path_traversal(tmp_path: Path) -> None:
    service = ObsidianService(tmp_path)

    with pytest.raises(ValueError, match="sort du vault"):
        service.read_note("../outside.md")


def test_write_note_requires_explicit_overwrite(tmp_path: Path) -> None:
    service = ObsidianService(tmp_path)
    service.write_note("Notion/Page.md", "première version")

    with pytest.raises(FileExistsError):
        service.write_note("Notion/Page.md", "seconde version")

    path = service.write_note("Notion/Page.md", "seconde version", overwrite=True)
    assert path == "Notion/Page.md"
    assert (tmp_path / path).read_text(encoding="utf-8") == "seconde version"
