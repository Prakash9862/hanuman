from pathlib import Path

from hanuman.services.atomic_write_service import atomic_write_text


def test_atomic_write_text_replaces_content_and_cleans_temporary_file(
    tmp_path: Path,
) -> None:
    path = tmp_path / "nested" / "note.md"
    path.parent.mkdir()
    path.write_text("ancienne version", encoding="utf-8")

    atomic_write_text(path, "nouvelle version")

    assert path.read_text(encoding="utf-8") == "nouvelle version"
    assert list(path.parent.glob(f".{path.name}.*.tmp")) == []
